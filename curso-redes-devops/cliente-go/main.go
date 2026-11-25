// cliente-go: el mismo GET que hace curl en la lección 4, pero con el TLS de Go.
// Go dejó de aceptar el nombre en el CN (sin SAN) en la 1.15: lo que curl da por bueno, Go no.
package main

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"os"
	"time"
)

func main() {
	raiz, err := os.ReadFile("/c/raiz.pem")
	if err != nil {
		fmt.Println("no leo la raíz:", err)
		os.Exit(2)
	}
	cas := x509.NewCertPool()
	cas.AppendCertsFromPEM(raiz)
	c := &http.Client{Timeout: 5 * time.Second, Transport: &http.Transport{TLSClientConfig: &tls.Config{RootCAs: cas}}}
	r, err := c.Get(os.Args[1])
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	r.Body.Close()
	fmt.Println(r.Status)
}
