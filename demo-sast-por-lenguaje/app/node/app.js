// ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.
const express = require("express");
const { exec } = require("child_process");
const sqlite3 = require("sqlite3");
const { buscarProductos } = require("./consultas");

const app = express();
const db = new sqlite3.Database("tienda.db");

app.get("/usuario", (req, res) => {
  // V1: inyección SQL
  const id = req.query.id;
  db.all("SELECT nombre FROM usuarios WHERE id = " + id, (err, filas) => res.json(filas));
});

app.get("/ping", (req, res) => {
  // V2: inyección de comandos
  const host = req.query.host;
  exec("ping -c 1 " + host, (err, salida) => res.send(salida));
});

app.get("/buscar", (req, res) => {
  // V3: inyección SQL a través de otro archivo
  buscarProductos(db, req.query.q, (filas) => res.json(filas));
});

app.get("/usuario_seguro", (req, res) => {
  // S1: consulta con parámetros: segura
  db.all("SELECT nombre FROM usuarios WHERE id = ?", [req.query.id], (err, filas) => res.json(filas));
});

app.get("/pedido", (req, res) => {
  // S2: el id se convierte a entero: seguro
  const id = parseInt(req.query.id, 10);
  db.all("SELECT total FROM pedidos WHERE id = " + id, (err, filas) => res.json(filas));
});

app.listen(3000);
