import express from 'express';
const app = express();
app.get('/', (_req, res) => { res.send('ok'); });
app.listen(8080, () => console.log('escuchando en 8080'));
