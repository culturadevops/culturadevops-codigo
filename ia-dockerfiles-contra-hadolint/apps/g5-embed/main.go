package main

import (
	"embed"
	"io/fs"
	"log"
	"net/http"
)

//go:embed static
var static embed.FS

func main() {
	sub, _ := fs.Sub(static, "static")
	http.Handle("/", http.FileServer(http.FS(sub)))
	log.Fatal(http.ListenAndServe(":8080", nil))
}
