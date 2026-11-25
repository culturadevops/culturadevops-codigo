// El servidor de la comparativa, en Node: SOLO librería estándar (node:http).
// El mismo contrato que el de Python: /suma hace CPU de verdad, /espera simula E/S.
const http = require('node:http');
const { URL } = require('node:url');

const ARRANQUE = process.hrtime.bigint();

const srv = http.createServer((req, res) => {
  const u = new URL(req.url, 'http://x');
  if (u.pathname === '/suma') {
    const n = Number(u.searchParams.get('n') || 0);
    const t0 = process.hrtime.bigint();
    let s = 0;
    for (let i = 1; i <= n; i++) {
      s += (i * i) % 1000003;
    }
    const ns = Number(process.hrtime.bigint() - t0);
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ lang: 'node', n, suma: s, ns }));
  } else if (u.pathname === '/espera') {
    const ms = Number(u.searchParams.get('ms') || 0);
    setTimeout(() => {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ lang: 'node', n: ms, suma: 0, ns: 0 }));
    }, ms);
  } else {
    res.statusCode = 404;
    res.end();
  }
});

srv.listen(8080, () => {
  // La marca de «listo» del propio proceso.
  const ms = Number(process.hrtime.bigint() - ARRANQUE) / 1e6;
  process.stderr.write(`LISTO_EN_MS ${ms.toFixed(3)}\n`);
});
