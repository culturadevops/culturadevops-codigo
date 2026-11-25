FROM node:22.12.0-bookworm-slim
WORKDIR /app
COPY . .
USER node
EXPOSE 8080
CMD ["node", "index.js"]
