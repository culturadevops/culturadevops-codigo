const Koa = require('koa');
const app = new Koa();
app.use(ctx => { ctx.body = 'ok'; });
app.listen(8080, () => console.log('escuchando en 8080'));
