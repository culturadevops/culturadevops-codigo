// Backend neutro para los bancos de proxies (cultura-devops 836-838): responde SIEMPRE el mismo cuerpo de 1 KiB en /api.
// Corre con más CPU que los proxies (6 contra 2) para que el cuello sea el proxy, no él; el banco mide su techo directo.
package main

import (
	"net/http"
	"strings"
)

func main() {
	cuerpo := []byte(strings.Repeat("0123456789abcdef", 64)) // 1.024 bytes
	http.HandleFunc("/api", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		w.Write(cuerpo)
	})
	if err := http.ListenAndServe(":9000", nil); err != nil {
		panic(err)
	}
}
