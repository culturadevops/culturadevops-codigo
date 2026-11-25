# Express sobre la slim oficial.
FROM node:22-slim
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev --no-audit --no-fund
COPY servidor.js .
EXPOSE 8080
CMD ["node", "servidor.js"]
