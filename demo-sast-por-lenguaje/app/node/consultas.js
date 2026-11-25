// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.

function buscarProductos(db, texto, listo) {
  // V3: el SQL se arma aquí, lejos de donde entra el dato
  const sql = "SELECT nombre FROM productos WHERE nombre LIKE '%" + texto + "%'";
  db.all(sql, (err, filas) => listo(filas));
}

module.exports = { buscarProductos };
