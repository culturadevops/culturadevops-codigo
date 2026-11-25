# Use la imagen base de Go
FROM golang:1.24 AS builder

# Establecer el trabajo de directorio de trabajo
WORKDIR /app

# Copiar el archivo go.mod y go.sum para que se instalen las dependencias
COPY go.mod go.sum ./

# Instalar las dependencias
RUN go mod download

# Copiar el código fuente
COPY . .

# Construir la aplicación
RUN go build -o api-gin .

# Use la imagen base de Alpine para la versión de producción
FROM alpine:latest

# Establecer el trabajo de directorio de trabajo
WORKDIR /root/

# Copiar la aplicación compilada desde el paso de construcción
COPY --from=builder /app/api-gin .

# Exponer el puerto 8080
EXPOSE 8080

# Ejecutar la aplicación
CMD ["./api-gin"]
