# Usar una imagen base de Node.js
FROM node:14

# Copiar el contenido del proyecto al directorio /app en la imagen
COPY . /app

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar las dependencias
RUN npm install

# Exponer el puerto 8080
EXPOSE 8080

# Comando a ejecutar la aplicación
CMD ["npm", "start"]
