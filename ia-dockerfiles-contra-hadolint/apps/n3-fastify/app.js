import Fastify from 'fastify';
const app = Fastify({ logger: true });
app.get('/', async () => 'ok');
await app.listen({ port: 8080, host: '0.0.0.0' });
