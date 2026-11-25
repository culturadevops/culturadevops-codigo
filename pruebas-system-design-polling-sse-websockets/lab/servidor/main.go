// servidor: una notificación nueva cada 3 s, que se puede recibir de cuatro maneras:
//
//	GET /poll                el último evento, al momento
//	GET /longpoll?desde=N    espera (hasta 30 s) a que haya un evento posterior a N
//	GET /sse                 Server-Sent Events: la conexión queda abierta y llega cada evento
//	GET /ws                  WebSocket: igual, por un canal en los dos sentidos
//
// /stats dice cuántas peticiones ha recibido y cuántas conexiones hay abiertas (y el máximo).
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
)

type evento struct {
	ID     int64 `json:"id"`
	Creado int64 `json:"creado"` // unix nanos
}

var (
	mu          sync.Mutex
	ultimo      evento
	subs        = map[chan evento]struct{}{}
	peticiones  atomic.Int64
	abiertas    atomic.Int64
	maxAbiertas atomic.Int64
)

func abrir() func() {
	n := abiertas.Add(1)
	for {
		m := maxAbiertas.Load()
		if n <= m || maxAbiertas.CompareAndSwap(m, n) {
			break
		}
	}
	return func() { abiertas.Add(-1) }
}

func suscribir() (chan evento, func()) {
	ch := make(chan evento, 16)
	mu.Lock()
	subs[ch] = struct{}{}
	mu.Unlock()
	return ch, func() { mu.Lock(); delete(subs, ch); mu.Unlock() }
}

func publicar() {
	for range time.Tick(3 * time.Second) {
		mu.Lock()
		ultimo = evento{ultimo.ID + 1, time.Now().UnixNano()}
		for ch := range subs {
			select {
			case ch <- ultimo:
			default:
			}
		}
		mu.Unlock()
	}
}

// rssKB: la memoria residente del proceso, de /proc/self/status.
func rssKB() int64 {
	b, _ := os.ReadFile("/proc/self/status")
	for _, l := range strings.Split(string(b), "\n") {
		if v, ok := strings.CutPrefix(l, "VmRSS:"); ok {
			n, _ := strconv.ParseInt(strings.TrimSpace(strings.TrimSuffix(strings.TrimSpace(v), "kB")), 10, 64)
			return n
		}
	}
	return 0
}

func actual() evento { mu.Lock(); defer mu.Unlock(); return ultimo }

func main() {
	go publicar()
	http.HandleFunc("/poll", func(w http.ResponseWriter, r *http.Request) {
		peticiones.Add(1)
		json.NewEncoder(w).Encode(actual())
	})
	http.HandleFunc("/longpoll", func(w http.ResponseWriter, r *http.Request) {
		peticiones.Add(1)
		defer abrir()()
		desde, _ := strconv.ParseInt(r.URL.Query().Get("desde"), 10, 64)
		if e := actual(); e.ID > desde {
			json.NewEncoder(w).Encode(e)
			return
		}
		ch, fin := suscribir()
		defer fin()
		select {
		case e := <-ch:
			json.NewEncoder(w).Encode(e)
		case <-time.After(30 * time.Second):
			w.WriteHeader(http.StatusNoContent)
		case <-r.Context().Done():
		}
	})
	http.HandleFunc("/sse", func(w http.ResponseWriter, r *http.Request) {
		peticiones.Add(1)
		defer abrir()()
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		// El flujo vacío siempre lo pide: si no, con HTTP/1.1 hacia aquí nginx no pasa ni las
		// cabeceras hasta que llega algo de cuerpo (medido), y la prueba no mediría el timeout.
		if r.URL.Query().Get("sin_buffer") == "1" || r.URL.Query().Get("vacio") == "1" {
			w.Header().Set("X-Accel-Buffering", "no") // pide a nginx que no acumule
		}
		f := w.(http.Flusher)
		f.Flush()
		if r.URL.Query().Get("vacio") == "1" { // un flujo que no manda nada: solo espera
			<-r.Context().Done()
			return
		}
		ch, fin := suscribir()
		defer fin()
		for {
			select {
			case e := <-ch:
				b, _ := json.Marshal(e)
				fmt.Fprintf(w, "data: %s\n\n", b)
				f.Flush()
			case <-r.Context().Done():
				return
			}
		}
	})
	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		peticiones.Add(1)
		c, err := websocket.Accept(w, r, nil)
		if err != nil {
			return
		}
		defer abrir()()
		defer c.CloseNow()
		ch, fin := suscribir()
		defer fin()
		ctx := c.CloseRead(context.Background())
		for {
			select {
			case e := <-ch:
				if wsjson.Write(ctx, c, e) != nil {
					return
				}
			case <-ctx.Done():
				return
			}
		}
	})
	http.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "%d %d %d %d\n", peticiones.Load(), abiertas.Load(), maxAbiertas.Load(), rssKB())
	})
	http.HandleFunc("/reset", func(w http.ResponseWriter, r *http.Request) {
		peticiones.Store(0)
		maxAbiertas.Store(abiertas.Load())
	})
	http.ListenAndServe(":8080", nil)
}
