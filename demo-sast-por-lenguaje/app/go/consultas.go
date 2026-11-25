// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.
package main

import "database/sql"

func buscarProductos(db *sql.DB, texto string) *sql.Rows {
	// V3: el SQL se arma aquí, lejos de donde entra el dato
	sql := "SELECT nombre FROM productos WHERE nombre LIKE '%" + texto + "%'"
	filas, _ := db.Query(sql)
	return filas
}
