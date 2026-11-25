# Un servidor Debian con nginx y certbot (con su plugin de nginx), como en un VPS recién instalado.
FROM debian:trixie-slim
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends nginx certbot python3-certbot-nginx curl openssl ca-certificates procps >/dev/null     && rm -rf /var/lib/apt/lists/*
COPY tienda.conf /etc/nginx/sites-available/tienda
RUN rm -f /etc/nginx/sites-enabled/default && ln -s /etc/nginx/sites-available/tienda /etc/nginx/sites-enabled/tienda     && mkdir -p /var/www/tienda && echo '<h1>Mi tienda</h1>' > /var/www/tienda/index.html
CMD ["nginx", "-g", "daemon off;"]
