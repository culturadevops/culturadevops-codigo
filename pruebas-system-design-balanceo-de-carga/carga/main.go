// carga: N peticiones con C clientes a la vez contra una URL. Dice p50, p99, errores y a qué
// réplica fue cada petición (cabecera X-Replica). Con -durante, mide en el tiempo: cada segundo,
// cuántas peticiones fallaron (para ver cuánto tarda el balanceador en retirar una réplica caída).
package main

import (
	"flag"
	"fmt"
	"io"
	"net/http"
	"sort"
	"strings"
	"sync"
	"time"
)

func main() {
	url := flag.String("url", "http://lb/", "a dónde")
	n := flag.Int("n", 2000, "peticiones")
	c := flag.Int("c", 20, "clientes a la vez")
	keep := flag.Bool("keepalive", true, "reutilizar conexiones (cada cliente, la suya)")
	durante := flag.Duration("durante", 0, "en vez de -n: pedir durante este tiempo y contar fallos por segundo")
	post := flag.Bool("post", false, "POST en vez de GET (no idempotente: un proxy no debería repetirlo)")
	morirA := flag.Duration("morir-a", 0, "a este tiempo de carga, pedir -morir-url (mata una réplica)")
	morirURL := flag.String("morir-url", "", "la URL /morir de la réplica que se cae")
	flag.Parse()

	var mu sync.Mutex
	var lat []time.Duration
	por := map[string]int{}
	errs := 0
	t0 := time.Now()
	fallosSeg := map[int]int{}
	okSeg := map[int]int{}

	if *morirA > 0 {
		go func() {
			time.Sleep(*morirA)
			http.Get(*morirURL) // la réplica responde y sale: a partir de aquí, conexión rechazada
		}()
	}

	var wg sync.WaitGroup
	cola := make(chan struct{}, *n)
	if *durante == 0 {
		for i := 0; i < *n; i++ {
			cola <- struct{}{}
		}
		close(cola)
	}
	for w := 0; w < *c; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			cli := &http.Client{Timeout: 5 * time.Second,
				Transport: &http.Transport{DisableKeepAlives: !*keep, MaxIdleConnsPerHost: 1}}
			una := func() {
				ini := time.Now()
				var resp *http.Response
				var err error
				if *post {
					resp, err = cli.Post(*url, "application/json", strings.NewReader(`{"pago":100}`))
				} else {
					resp, err = cli.Get(*url)
				}
				d := time.Since(ini)
				seg := int(time.Since(t0).Seconds())
				mu.Lock()
				defer mu.Unlock()
				if err != nil || resp.StatusCode != 200 {
					errs++
					fallosSeg[seg]++
					if resp != nil {
						resp.Body.Close()
					}
					return
				}
				io.Copy(io.Discard, resp.Body)
				resp.Body.Close()
				lat = append(lat, d)
				por[resp.Header.Get("X-Replica")]++
				okSeg[seg]++
			}
			if *durante > 0 {
				for time.Since(t0) < *durante {
					una()
				}
				return
			}
			for range cola {
				una()
			}
		}()
	}
	wg.Wait()

	if *durante > 0 {
		var segs []int
		for s := range okSeg {
			segs = append(segs, s)
		}
		for s := range fallosSeg {
			if okSeg[s] == 0 {
				segs = append(segs, s)
			}
		}
		sort.Ints(segs)
		for _, s := range segs {
			fmt.Printf("  segundo %2d: %4d bien · %3d fallos\n", s, okSeg[s], fallosSeg[s])
		}
	}
	sort.Slice(lat, func(i, j int) bool { return lat[i] < lat[j] })
	pct := func(p float64) time.Duration {
		if len(lat) == 0 {
			return 0
		}
		return lat[int(float64(len(lat)-1)*p)]
	}
	var reps []string
	for k := range por {
		reps = append(reps, k)
	}
	sort.Strings(reps)
	var dist []string
	for _, k := range reps {
		dist = append(dist, fmt.Sprintf("%s %d", k, por[k]))
	}
	fmt.Printf("  %d bien · %d fallos · p50 %v · p99 %v · total %v\n", len(lat), errs,
		pct(0.50).Round(time.Millisecond), pct(0.99).Round(time.Millisecond), time.Since(t0).Round(100*time.Millisecond))
	fmt.Printf("  reparto: %s\n", strings.Join(dist, " · "))
}
