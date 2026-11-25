// El servidor de la revancha, lado Node: Express.
// Mismo contrato que el 152: /suma hace CPU de verdad, /espera simula E/S.
const express = require('express');

const ARRANQUE = process.hrtime.bigint();
const app = express();

app.get('/suma', (req, res) => {
  const n = Number(req.query.n || 0);
  const t0 = process.hrtime.bigint();
  let s = 0;
  for (let i = 1; i <= n; i++) {
    s += (i * i) % 1000003;
  }
  const ns = Number(process.hrtime.bigint() - t0);
  res.json({ lang: 'express', n, suma: s, ns });
});

app.get('/espera', (req, res) => {
  const ms = Number(req.query.ms || 0);
  setTimeout(() => res.json({ lang: 'express', n: ms, suma: 0, ns: 0 }), ms);
});

app.listen(8080, () => {
  const ms = Number(process.hrtime.bigint() - ARRANQUE) / 1e6;
  process.stderr.write(`LISTO_EN_MS ${ms.toFixed(3)}\n`);
});
