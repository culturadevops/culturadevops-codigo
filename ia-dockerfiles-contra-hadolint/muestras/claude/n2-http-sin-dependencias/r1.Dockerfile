FROM node:22-alpine3.22

ENV NODE_ENV=production

RUN apk add --no-cache tini=0.19.0-r3

WORKDIR /app

COPY --chown=node:node package.json ./
COPY --chown=node:node index.js ./

USER node

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/ || exit 1

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "index.js"]
