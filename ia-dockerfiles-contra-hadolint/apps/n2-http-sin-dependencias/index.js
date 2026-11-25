const http = require('http');
http.createServer((req, res) => { res.end('ok'); }).listen(8080, () => console.log('escuchando en 8080'));
