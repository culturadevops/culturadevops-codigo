// La misma tienda, con los fallos arreglados (demo de cultura-devops).
const express = require('express');
const mysql = require('mysql2');
const { execFile } = require('child_process');
const fs = require('fs');
const net = require('net');
const path = require('path');

const app = express();
const db = mysql.createConnection({ host: 'db', user: 'tienda', database: 'tienda' });
// Arreglo 4: la clave viene del entorno (en el pipeline, de un gestor de secretos)
const STRIPE_API_KEY = process.env.STRIPE_API_KEY;
const FACTURAS = path.resolve('/srv/facturas');

app.get('/producto', (req, res) => {
  // Arreglo 1: consulta con parámetros
  db.execute('SELECT id, nombre, precio FROM productos WHERE nombre = ?', [String(req.query.nombre)], (err, filas) => res.json(filas));
});

app.get('/ping', (req, res) => {
  // Arreglo 2: solo IPs, y execFile sin shell
  const host = String(req.query.host);
  if (net.isIP(host) === 0) return res.status(400).send('IP no válida');
  execFile('ping', ['-c', '1', host], (err, salida) => res.send(salida));
});

app.get('/factura', (req, res) => {
  // Arreglo 3: la ruta final tiene que quedar dentro de FACTURAS
  const ruta = path.resolve(FACTURAS, path.basename(String(req.query.archivo))); // njsscan-ignore: join_resolve_path_traversal
  if (!ruta.startsWith(FACTURAS + path.sep)) return res.status(404).end();
  res.send(fs.readFileSync(ruta, 'utf8')); // njsscan-ignore: generic_path_traversal, express_xss
});

app.post('/preferencias', express.json(), (req, res) => {
  const { tema, idioma } = req.body;
  res.json({ tema: String(tema), idioma: String(idioma) });
});

app.listen(3000);
