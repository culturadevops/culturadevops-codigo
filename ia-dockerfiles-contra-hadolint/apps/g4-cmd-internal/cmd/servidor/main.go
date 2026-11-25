package main

import (
	"log"
	"net/http"

	"ejemplo.com/servicio/internal/saludo"
)

func main() {
	http.HandleFunc("/", saludo.Handler)
	log.Fatal(http.ListenAndServe(":8080", nil))
}
