# Use la imagen base de Go
FROM golang:1.24 AS builder

# Establecer el trabajo de directorio de trabajo
WORKDIR /app

# Copiar el archivo go.mod y ejecutar mod tidy
COPY go.mod go.sum ./
RUN go mod download

# Copiar el código fuente
COPY . .

# Construir la aplicación
RUN go build -o servidor cmd/servidor/main.go

# Crear una nueva imagen de producción
FROM alpine:latest

# Establecer el trabajo de directorio de trabajo
WORKDIR /root/

# Copiar la aplicación compilada desde el paso de construcción
COPY --from=builder /app/servidor .

# Exponer el puerto 8080
EXPOSE 8080

# Ejecutar la aplicación
CMD ["./servidor"]
