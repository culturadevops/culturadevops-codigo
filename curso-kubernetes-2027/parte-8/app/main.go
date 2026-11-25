// k8s-b-api: la app del banco de las partes 7 y 8 del «Curso de Kubernetes 2027» (cultura-devops).
// Una API mínima con lo que hace falta para medir probes, recursos, HPA y el proyecto final.
//
//	GET  /            quién soy (pod, versión, mensaje de la configuración)
//	GET  /salud       liveness: 200, o se cuelga si alguien llamó a /colgar
//	GET  /listo       readiness: 200 si arrancó, no está «fuera» y (si hay BD) la BD responde
//	POST /fuera       readiness pasa a 503 (el proceso sigue sano)
//	POST /colgar      /salud deja de responder (proceso vivo pero colgado)
//	GET  /cpu?n=N     trabajo de CPU fijo: N rondas de sha256
//	GET  /mem?mb=N    reserva y toca N MiB y los retiene
//	GET  /items       lista de la BD · POST /items?nombre=x inserta
package main

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync/atomic"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"
)

var (
	fuera   atomic.Bool
	colgado atomic.Bool
	db      *sql.DB
	retener [][]byte
	inicio  = time.Now()
)

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func js(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func main() {
	if s, _ := strconv.Atoi(env("ARRANQUE_SEGUNDOS", "0")); s > 0 {
		log.Printf("arrancando: %d s de preparación antes de escuchar", s)
		time.Sleep(time.Duration(s) * time.Second)
	}
	if dsn := os.Getenv("DATABASE_URL"); dsn != "" {
		var err error
		db, err = sql.Open("pgx", dsn)
		if err != nil {
			log.Fatal(err)
		}
		db.SetMaxOpenConns(5)
		db.SetConnMaxLifetime(30 * time.Second)
	}
	host, _ := os.Hostname()
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
		js(w, 200, map[string]any{"pod": host, "version": env("VERSION", "1"), "mensaje": env("MENSAJE", "")})
	})
	mux.HandleFunc("GET /salud", func(w http.ResponseWriter, r *http.Request) {
		if colgado.Load() {
			select {} // vivo pero sin responder
		}
		fmt.Fprintln(w, "ok")
	})
	mux.HandleFunc("GET /listo", func(w http.ResponseWriter, r *http.Request) {
		if fuera.Load() {
			http.Error(w, "fuera de servicio", 503)
			return
		}
		if db != nil {
			ctx, cancel := context.WithTimeout(r.Context(), 800*time.Millisecond)
			defer cancel()
			if err := db.PingContext(ctx); err != nil {
				http.Error(w, "sin base de datos", 503)
				return
			}
		}
		fmt.Fprintln(w, "listo")
	})
	mux.HandleFunc("POST /fuera", func(w http.ResponseWriter, r *http.Request) { fuera.Store(true); fmt.Fprintln(w, "fuera") })
	mux.HandleFunc("POST /colgar", func(w http.ResponseWriter, r *http.Request) { colgado.Store(true); fmt.Fprintln(w, "colgado") })
	mux.HandleFunc("GET /cpu", func(w http.ResponseWriter, r *http.Request) {
		n, _ := strconv.Atoi(r.URL.Query().Get("n"))
		if n <= 0 {
			n = 100000
		}
		t := time.Now()
		h := sha256.Sum256([]byte(host))
		for i := 0; i < n; i++ {
			h = sha256.Sum256(h[:])
		}
		fmt.Fprintf(w, "%d rondas en %d ms (%x)\n", n, time.Since(t).Milliseconds(), h[:2])
	})
	mux.HandleFunc("GET /mem", func(w http.ResponseWriter, r *http.Request) {
		mb, _ := strconv.Atoi(r.URL.Query().Get("mb"))
		for i := 0; i < mb; i++ {
			b := make([]byte, 1<<20)
			for j := range b {
				b[j] = byte(j)
			}
			retener = append(retener, b)
		}
		fmt.Fprintf(w, "retengo %d MiB\n", len(retener))
	})
	mux.HandleFunc("GET /items", func(w http.ResponseWriter, r *http.Request) {
		if db == nil {
			http.Error(w, "sin BD", 500)
			return
		}
		rows, err := db.QueryContext(r.Context(), "SELECT id, nombre FROM items ORDER BY id")
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()
		type it struct {
			ID     int    `json:"id"`
			Nombre string `json:"nombre"`
		}
		out := []it{}
		for rows.Next() {
			var x it
			_ = rows.Scan(&x.ID, &x.Nombre)
			out = append(out, x)
		}
		js(w, 200, map[string]any{"pod": host, "items": out})
	})
	mux.HandleFunc("POST /items", func(w http.ResponseWriter, r *http.Request) {
		if db == nil {
			http.Error(w, "sin BD", 500)
			return
		}
		var id int
		err := db.QueryRowContext(r.Context(), "INSERT INTO items(nombre) VALUES($1) RETURNING id", r.URL.Query().Get("nombre")).Scan(&id)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		js(w, 201, map[string]any{"pod": host, "id": id})
	})
	if db != nil {
		go func() { // crea la tabla en cuanto la BD responda
			for {
				if _, err := db.Exec("CREATE TABLE IF NOT EXISTS items(id serial PRIMARY KEY, nombre text NOT NULL)"); err == nil {
					return
				}
				time.Sleep(2 * time.Second)
			}
		}()
	}
	log.Printf("escuchando en :8080 tras %d ms", time.Since(inicio).Milliseconds())
	log.Fatal(http.ListenAndServe(":8080", mux))
}
