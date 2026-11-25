// cliente: N clientes reciben las notificaciones de una manera durante un tiempo. Mide cuántos
// eventos recibe cada uno y cuánto tarda en enterarse (desde que el servidor lo creó).
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

// conn cuenta los bytes que pasan por el socket, en los dos sentidos (cabeceras incluidas).
type conn struct {
	net.Conn
}

var bytesRed atomic.Int64

func (c conn) Read(b []byte) (int, error) {
	n, err := c.Conn.Read(b)
	bytesRed.Add(int64(n))
	return n, err
}
func (c conn) Write(b []byte) (int, error) {
	n, err := c.Conn.Write(b)
	bytesRed.Add(int64(n))
	return n, err
}

func transporte() *http.Transport {
	d := &net.Dialer{}
	return &http.Transport{DialContext: func(ctx context.Context, red, dir string) (net.Conn, error) {
		cn, err := d.DialContext(ctx, red, dir)
		if err != nil {
			return nil, err
		}
		return conn{cn}, nil
	}}
}

type evento struct {
	ID     int64 `json:"id"`
	Creado int64 `json:"creado"`
}

func main() {
	modo := flag.String("modo", "poll", "poll, longpoll, sse, ws, silencio")
	base := flag.String("url", "http://srv:8080", "servidor (o proxy)")
	cada := flag.Duration("cada", 5*time.Second, "poll: cada cuánto se pregunta")
	n := flag.Int("clientes", 100, "clientes a la vez")
	durante := flag.Duration("durante", 30*time.Second, "cuánto tiempo")
	sinBuffer := flag.Bool("sin-buffer", false, "sse: pedir X-Accel-Buffering: no")
	flag.Parse()

	if strings.HasPrefix(*modo, "memoria-") { // memoria-sse o memoria-ws: N conexiones abiertas
		tipo := strings.TrimPrefix(*modo, "memoria-")
		leer := func() (int64, int64) {
			var pet, ab, mx, rss int64
			if r, err := http.Get(*base + "/stats"); err == nil {
				fmt.Fscan(r.Body, &pet, &ab, &mx, &rss)
				r.Body.Close()
			}
			return ab, rss
		}
		_, antes := leer()
		ctx, cancel := context.WithCancel(context.Background())
		for i := 0; i < *n; i++ {
			go func() {
				if tipo == "ws" {
					if c, _, err := websocket.Dial(ctx, strings.Replace(*base, "http", "ws", 1)+"/ws", nil); err == nil {
						defer c.CloseNow()
						var e evento
						for wsjson.Read(ctx, c, &e) == nil {
						}
					}
					return
				}
				req, _ := http.NewRequestWithContext(ctx, "GET", *base+"/sse", nil)
				if r, err := http.DefaultClient.Do(req); err == nil {
					b := make([]byte, 512)
					for {
						if _, err := r.Body.Read(b); err != nil {
							return
						}
					}
				}
			}()
		}
		time.Sleep(8 * time.Second)
		ab, despues := leer()
		cancel()
		fmt.Printf("  %-3s %d conexiones abiertas · memoria del servidor: %d MB antes, %d MB con ellas · %.1f KB por conexión\n",
			tipo, ab, antes/1024, despues/1024, float64(despues-antes)/float64(max(ab, 1)))
		return
	}
	if *modo == "silencio" { // un flujo SSE sin eventos: ¿cuánto aguanta abierto?
		t0 := time.Now()
		ctx, cancel := context.WithTimeout(context.Background(), *durante)
		defer cancel()
		req, _ := http.NewRequestWithContext(ctx, "GET", *base+"/sse?vacio=1", nil)
		r, err := http.DefaultClient.Do(req)
		if err != nil {
			fmt.Printf("  silencio: error al conectar: %v\n", err)
			return
		}
		b := make([]byte, 512)
		var e error
		for e == nil {
			_, e = r.Body.Read(b)
		}
		if ctx.Err() != nil {
			fmt.Printf("  silencio: la conexión sigue abierta a los %v (fin de la prueba)\n", time.Since(t0).Round(time.Second))
		} else {
			fmt.Printf("  silencio: la conexión se cortó a los %v · %v\n", time.Since(t0).Round(time.Second), e)
		}
		return
	}
	if r, err := http.Get(*base + "/reset"); err == nil {
		r.Body.Close()
	}
	ctx, cancel := context.WithTimeout(context.Background(), *durante)
	defer cancel()
	var mu sync.Mutex
	var retrasos []time.Duration
	errores := ""
	inicio := time.Now()

	anotar := func(visto map[int64]bool, e evento) {
		if e.ID == 0 || visto[e.ID] || e.Creado < inicio.UnixNano() {
			return
		}
		visto[e.ID] = true
		d := time.Since(time.Unix(0, e.Creado))
		mu.Lock()
		retrasos = append(retrasos, d)
		mu.Unlock()
	}
	fallo := func(err error) {
		mu.Lock()
		if errores == "" {
			errores = err.Error()
		}
		mu.Unlock()
	}
	var wg sync.WaitGroup
	for i := 0; i < *n; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			visto := map[int64]bool{}
			cli := &http.Client{Transport: transporte()}
			switch *modo {
			case "poll":
				for ctx.Err() == nil {
					if r, err := cli.Get(*base + "/poll"); err == nil {
						var e evento
						json.NewDecoder(r.Body).Decode(&e)
						r.Body.Close()
						anotar(visto, e)
					}
					select {
					case <-time.After(*cada):
					case <-ctx.Done():
					}
				}
			case "longpoll":
				var desde int64
				for ctx.Err() == nil {
					req, _ := http.NewRequestWithContext(ctx, "GET", *base+"/longpoll?desde="+strconv.FormatInt(desde, 10), nil)
					r, err := cli.Do(req)
					if err != nil {
						continue
					}
					var e evento
					if r.StatusCode == 200 {
						json.NewDecoder(r.Body).Decode(&e)
						anotar(visto, e)
						desde = e.ID
					}
					r.Body.Close()
				}
			case "sse":
				u := *base + "/sse"
				if *sinBuffer {
					u += "?sin_buffer=1"
				}
				req, _ := http.NewRequestWithContext(ctx, "GET", u, nil)
				r, err := cli.Do(req)
				if err != nil {
					fallo(err)
					return
				}
				defer r.Body.Close()
				s := bufio.NewScanner(r.Body)
				for s.Scan() {
					if l, ok := strings.CutPrefix(s.Text(), "data: "); ok {
						var e evento
						json.Unmarshal([]byte(l), &e)
						anotar(visto, e)
					}
				}
			case "ws":
				c, _, err := websocket.Dial(ctx, strings.Replace(*base, "http", "ws", 1)+"/ws",
					&websocket.DialOptions{HTTPClient: &http.Client{Transport: transporte()}})
				if err != nil {
					fallo(err)
					return
				}
				defer c.CloseNow()
				for {
					var e evento
					if wsjson.Read(ctx, c, &e) != nil {
						return
					}
					anotar(visto, e)
				}
			}
		}()
	}
	wg.Wait()
	var pet, abiertas, maxAb, rss int64
	if r, err := http.Get(*base + "/stats"); err == nil {
		fmt.Fscan(r.Body, &pet, &abiertas, &maxAb, &rss)
		r.Body.Close()
	}
	sort.Slice(retrasos, func(i, j int) bool { return retrasos[i] < retrasos[j] })
	var suma time.Duration
	for _, d := range retrasos {
		suma += d
	}
	media, peor := time.Duration(0), time.Duration(0)
	if len(retrasos) > 0 {
		media, peor = suma/time.Duration(len(retrasos)), retrasos[len(retrasos)-1]
	}
	etiqueta := *modo
	if *modo == "poll" {
		etiqueta += " cada " + cada.String()
	}
	fmt.Printf("  %-12s %d clientes · %s: %4d eventos recibidos · retraso medio %v · peor %v · %d peticiones/min · conexiones abiertas a la vez: %d\n",
		etiqueta, *n, durante.String(), len(retrasos), media.Round(time.Millisecond), peor.Round(time.Millisecond),
		int64(float64(pet)/durante.Minutes()), maxAb)
	if len(retrasos) > 0 {
		fmt.Printf("               bytes en la red: %d KB en total · %d bytes por evento recibido\n",
			bytesRed.Load()/1024, bytesRed.Load()/int64(len(retrasos)))
	}
	if errores != "" {
		fmt.Printf("  error: %s\n", errores)
	}
}
