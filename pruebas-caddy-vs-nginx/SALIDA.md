# Salida ejecutada — vídeo 231 «Caddy, ¿la alternativa a Nginx este 2026?»

> Corrida del 2026-09-09. Caddy 2 y nginx, cada uno en su contenedor, sirviendo **lo mismo**: un
> sitio por HTTPS con certificado y un proxy inverso a un backend. Reproducible con `bash demo.sh`.

---

## ✅ Los dos sirven exactamente lo mismo

```
   Caddy, la pagina:      <h1>hola</h1>
   nginx, la pagina:      <h1>hola</h1>
   Caddy, el proxy /api/: <title>Welcome to nginx!</title>
   nginx, el proxy /api/: <title>Welcome to nginx!</title>
```

⚠️ **Y llegar aquí me costó dos correcciones**, las dos mías:

1. **Medía cada lado con una herramienta distinta.** Usaba el `wget` de cada imagen, y el de
   `nginx:alpine` **no habla HTTPS**. El resultado decía que nginx no servía nada. Servía. Ahora
   todas las comprobaciones salen de un **tercer contenedor neutral** con el mismo `curl`.
2. **Mis dos configuraciones no hacían lo mismo.** nginx, con la barra final en
   `proxy_pass http://backend:80/`, **quita** el prefijo `/api/`; Caddy con `reverse_proxy` no.
   Uno devolvía 404 y el otro la página del backend. Se arregló con `handle_path`, que es el
   equivalente exacto. 🥇 **Y esa barra final de nginx es de las cosas que más confunden a la
   gente**: va en el vídeo.

---

## 🥇 LA TABLA

| | Caddy | nginx | |
|---|---|---|---|
| líneas de configuración | **7** | 16 | 2,3× menos |
| pasos humanos hasta HTTPS | **1** | 4 | |
| de cero a servir por HTTPS | **666 ms** | 1.121 ms | (402 del certificado + 719 de arrancar) |
| **memoria en reposo** | 17,45 MB | **2,93 MB** | **nginx usa 6× MENOS** |
| tamaño de la imagen | **88,7 MB** | 103 MB | |
| ¿el certificado sale solo? | **sí** | no | |

## 🥇 EL RESULTADO QUE VA CONTRA EL TÓPICO

**nginx gasta seis veces menos memoria que Caddy.** 2,93 MB contra 17,45.

Va justo en contra de lo que se asume («la herramienta moderna en Go es ligera, nginx es el viejo
pesado»). nginx es C con veinte años de afinado; Caddy trae dentro un cliente de ACME, una
autoridad certificadora, gestión automática de certificados y una API de administración. Todo eso
ocupa, y lo ocupa **aunque no lo uses**.

## 🥇 LO QUE DE VERDAD COMPRA CADDY: los pasos, no los milisegundos

```
   Caddy → 1 paso:  escribir 7 líneas. No hay paso 2.
   nginx → 4 pasos: generar la clave · generar y firmar el certificado ·
                    escribir 16 líneas apuntando a los dos ficheros ·
                    y renovarlo dentro de 365 días, a mano
```

La diferencia de tiempo (666 ms contra 1.121) es irrelevante: los dos son instantáneos. **Lo que
cambia es el cuarto paso de nginx, el que no tiene fecha en el calendario de nadie.**

## Los dos certificados, y una diferencia que sorprende

```
   Caddy:  issuer = CN=Caddy Local Authority - ECC Intermediate
           notBefore = Sep  9 21:14:50 2026 GMT
           notAfter  = Sep 10 09:14:50 2026 GMT      <- ¡12 HORAS!

   nginx:  issuer = CN=sitio.local   (autofirmado por mí)
           notAfter = Sep  9 21:14:51 2027 GMT       <- 1 año
```

El de Caddy dura **doce horas** y el de nginx un año. Y sin embargo el que te va a dar un
disgusto es el de nginx. Porque el de Caddy se renueva solo, cada pocas horas, y nunca te enteras;
el de nginx caduca dentro de un año, cuando ya nadie se acuerde de que lo generó.

## 🥇 EL QUE NO SALE EN NINGUNA COMPARACIÓN

Tiro el backend y **reinicio los dos**:

```
   Caddy: Up 6 seconds
          y sigue sirviendo la pagina: <h1>hola</h1>

   nginx: Exited (1) 2 seconds ago
          nginx: [emerg] host not found in upstream "backend" in /etc/nginx/nginx.conf:15
```

**nginx resuelve los nombres de sus destinos al cargar la configuración, y se niega a arrancar si
alguno no resuelve.** Caddy los resuelve cuando llega una petición.

Eso es el problema del orden de arranque que muerde a todo el mundo con contenedores: reinicias la
máquina, tu proxy arranca antes que el servicio de detrás, y el proxy **no levanta**. Con Caddy
levanta y sirve lo que puede.

---

## ⛔ Lo que NO mide este banco

- **Rendimiento a escala.** Aquí se sirve una página a un cliente. nginx lleva veinte años siendo
  la referencia sirviendo estáticos a mucha carga, y eso no se ve en esta prueba.
- **El ecosistema de recetas.** Cualquier cosa rara que necesites tiene una respuesta de nginx en
  internet desde hace años. Con Caddy, a veces no.
- **HTTPS de verdad contra Let's Encrypt**, que necesita un dominio público. Aquí se usa la
  autoridad interna de Caddy, que es **el mismo mecanismo** menos la parte del dominio.

## ⚠️ Y repartir territorio con el vídeo 79 (Traefik)

El canal ya tiene `traefik-alternativa-a-nginx-2026`. No son el mismo reemplazo:
**Traefik** nació para descubrir contenedores solo y configurarse a partir de sus etiquetas.
**Caddy** nació para servir sitios con HTTPS sin que escribas configuración. Se dice en el vídeo.
