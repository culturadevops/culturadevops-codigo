// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.
package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os/exec"
	"strconv"

	"golang.org/x/text/language"
)

var db *sql.DB

func usuario(w http.ResponseWriter, r *http.Request) {
	// V1: inyección SQL
	id := r.URL.Query().Get("id")
	filas, _ := db.Query("SELECT nombre FROM usuarios WHERE id = " + id)
	fmt.Fprint(w, filas)
}

func ping(w http.ResponseWriter, r *http.Request) {
	// V2: inyección de comandos
	host := r.URL.Query().Get("host")
	salida, _ := exec.Command("sh", "-c", "ping -c 1 "+host).Output()
	w.Write(salida)
}

func buscar(w http.ResponseWriter, r *http.Request) {
	// V3: inyección SQL a través de otro archivo
	fmt.Fprint(w, buscarProductos(db, r.URL.Query().Get("q")))
}

func usuarioSeguro(w http.ResponseWriter, r *http.Request) {
	// S1: consulta con parámetros: segura
	filas, _ := db.Query("SELECT nombre FROM usuarios WHERE id = ?", r.URL.Query().Get("id"))
	fmt.Fprint(w, filas)
}

func pedido(w http.ResponseWriter, r *http.Request) {
	// S2: el id se convierte a entero: seguro
	id, err := strconv.Atoi(r.URL.Query().Get("id"))
	if err != nil {
		http.Error(w, "id inválido", http.StatusBadRequest)
		return
	}
	filas, _ := db.Query("SELECT total FROM pedidos WHERE id = " + strconv.Itoa(id))
	fmt.Fprint(w, filas)
}

func idioma(w http.ResponseWriter, r *http.Request) {
	// La dependencia vieja (golang.org/x/text v0.3.5): language.Parse con texto del usuario
	etiqueta, _ := language.Parse(r.Header.Get("Accept-Language"))
	fmt.Fprint(w, etiqueta)
}

func main() {
	db, _ = sql.Open("sqlite", "tienda.db")
	http.HandleFunc("/usuario", usuario)
	http.HandleFunc("/ping", ping)
	http.HandleFunc("/buscar", buscar)
	http.HandleFunc("/usuario_seguro", usuarioSeguro)
	http.HandleFunc("/pedido", pedido)
	http.HandleFunc("/idioma", idioma)
	http.ListenAndServe("127.0.0.1:8080", nil)
}
