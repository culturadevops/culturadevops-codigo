# La máquina del operador: el cliente de Postgres 17 (el mismo que el servidor: pg_dump de una
# versión más vieja que el servidor se niega a copiar), los binarios del servidor para levantar
# una restauración aparte, git, age y gzip.
FROM postgres:17
RUN apt-get update \
 && apt-get install -y --no-install-recommends git age gzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN git config --system user.email "curso@ejemplo.dev" \
 && git config --system user.name "Curso" \
 && git config --system init.defaultBranch main \
 && git config --system advice.detachedHead false
WORKDIR /trabajo
