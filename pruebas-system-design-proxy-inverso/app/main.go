// app: la aplicación detrás del proxy. Dos instancias (app1, app2) comparten /datos.
//
//	GET  /ip              qué IP de cliente ve la aplicación, y las cabeceras X-Forwarded-*
//	GET  /lento?s=70      responde a los s segundos
//	GET  /grande?mb=50    manda mb megas lo más rápido que puede, y anota cuánto tardó en soltarlos
//	GET  /procesar?s=3    «procesa» (anota una línea en /datos/procesados.log) y tarda s segundos
//	POST /pagar?s=3       cobra (anota una línea en /datos/pagos.log) y tarda s segundos en contestar
//	POST /subir           acepta un cuerpo y dice cuántos bytes llegaron
package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

var nombre = os.Getenv("NOMBRE")

func anotar(fichero, que string) {
	f, err := os.OpenFile("/datos/"+fichero, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	fmt.Fprintf(f, "%s %s %s\n", time.Now().Format("15:04:05.000"), nombre, que)
}

func segundos(r *http.Request) time.Duration {
	s, _ := strconv.ParseFloat(r.URL.Query().Get("s"), 64)
	return time.Duration(s * float64(time.Second))
}

func main() {
	http.HandleFunc("/ip", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "%s ve: RemoteAddr=%s · X-Forwarded-For=%q · X-Real-IP=%q · X-Forwarded-Proto=%q\n",
			nombre, strings.Split(r.RemoteAddr, ":")[0], r.Header.Get("X-Forwarded-For"),
			r.Header.Get("X-Real-IP"), r.Header.Get("X-Forwarded-Proto"))
	})
	http.HandleFunc("/lento", func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(segundos(r))
		fmt.Fprintln(w, "hecho")
	})
	http.HandleFunc("/grande", func(w http.ResponseWriter, r *http.Request) {
		mb, _ := strconv.Atoi(r.URL.Query().Get("mb"))
		t0 := time.Now()
		trozo := make([]byte, 1<<20)
		for i := 0; i < mb; i++ {
			if _, err := w.Write(trozo); err != nil {
				break
			}
		}
		anotar("grande.log", fmt.Sprintf("soltó %d MB en %.1f s", mb, time.Since(t0).Seconds()))
	})
	http.HandleFunc("/procesar", func(w http.ResponseWriter, r *http.Request) {
		anotar("procesados.log", "procesado")
		time.Sleep(segundos(r))
		fmt.Fprintln(w, "procesado")
	})
	http.HandleFunc("/pagar", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "solo POST", http.StatusMethodNotAllowed)
			return
		}
		anotar("pagos.log", "cobrado")
		time.Sleep(segundos(r))
		fmt.Fprintln(w, "cobrado")
	})
	http.HandleFunc("/subir", func(w http.ResponseWriter, r *http.Request) {
		n, _ := io.Copy(io.Discard, r.Body)
		fmt.Fprintf(w, "llegaron %d bytes\n", n)
	})
	http.ListenAndServe(":8000", nil)
}
