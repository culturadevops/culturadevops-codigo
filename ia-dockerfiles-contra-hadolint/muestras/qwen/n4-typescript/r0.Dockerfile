# Usar una imagen base de Node.js
FROM node:18-alpine

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /usr/src/app

# Copiar el archivo package.json y package-lock.json y instalar las dependencias
COPY package*.json ./
RUN npm ci

# Copiar el código fuente
COPY . .

# Compilar el TypeScript
RUN npm run build

# Establecer los puertos que el contenedor va a escuchar
EXPOSE 8080

# Comando a ejecutar cuando se ejecute el contenedor
CMD ["npm", "start"]
