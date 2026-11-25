// Tienda de ejemplo con 4 fallos de seguridad PUESTOS A PROPÓSITO (demo de cultura-devops). No la despliegues.
const express = require('express');
const mysql = require('mysql2');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const _ = require('lodash');

const app = express();
const db = mysql.createConnection({ host: 'db', user: 'tienda', database: 'tienda' });
// Fallo 4: una clave pegada en el código
const STRIPE_API_KEY = 'CLAVE_STRIPE_FALSA_DE_EJEMPLO';

app.get('/producto', (req, res) => {
  // Fallo 1: inyección SQL (el texto del usuario va pegado dentro de la consulta)
  db.query(`SELECT id, nombre, precio FROM productos WHERE nombre = '${req.query.nombre}'`, (err, filas) => res.json(filas));
});

app.get('/ping', (req, res) => {
  // Fallo 2: inyección de comandos
  exec('ping -c 1 ' + req.query.host, (err, salida) => res.send(salida));
});

app.get('/factura', (req, res) => {
  // Fallo 3: path traversal (archivo=../../etc/passwd sale de la carpeta)
  res.send(fs.readFileSync(path.join('/srv/facturas', req.query.archivo), 'utf8'));
});

app.post('/preferencias', express.json(), (req, res) => {
  // Extra: mezcla un objeto que manda el usuario (con lodash vulnerable, prototype pollution)
  res.json(_.merge({}, req.body));
});

app.listen(3000);
