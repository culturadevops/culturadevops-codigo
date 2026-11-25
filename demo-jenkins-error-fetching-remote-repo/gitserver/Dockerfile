# Un servidor git propio: HTTP (git-http-backend detrás de nginx, con un repo público y otro con contraseña) y SSH (usuario git).
FROM alpine:3.22
RUN apk add --no-cache git git-daemon nginx fcgiwrap spawn-fcgi openssh apache2-utils >/dev/null     && adduser -D -s /usr/bin/git-shell git && passwd -u git >/dev/null 2>&1; ssh-keygen -A >/dev/null
COPY nginx.conf /etc/nginx/http.d/default.conf
COPY iniciar.sh /iniciar.sh
RUN chmod +x /iniciar.sh
CMD ["/iniciar.sh"]
