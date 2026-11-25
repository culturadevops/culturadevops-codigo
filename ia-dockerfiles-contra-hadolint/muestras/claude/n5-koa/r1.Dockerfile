# syntax=docker/dockerfile:1

FROM node:22-alpine3.22 AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

FROM node:22-alpine3.22
ENV NODE_ENV=production
WORKDIR /app
# Versión de tini fijada para Alpine 3.22; si cambias la versión de Alpine, actualízala (apk policy tini)
RUN apk add --no-cache tini=0.19.0-r3
COPY --from=deps --chown=node:node /app/node_modules ./node_modules
COPY --chown=node:node package.json server.js ./
USER node
EXPOSE 8080
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
