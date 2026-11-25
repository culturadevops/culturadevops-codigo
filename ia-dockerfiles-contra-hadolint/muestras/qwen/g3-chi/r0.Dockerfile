# Use la imagen base de Go
FROM golang:1.24 AS builder

# Establece el trabajo de directorio de trabajo
WORKDIR /app

# Copia el archivo go.mod y go.sum
COPY go.mod go.sum ./

# Instala las dependencias
RUN go mod download

# Copia todos los archivos del proyecto
COPY . .

# Construye la aplicación
RUN go build -o api-chi .

# Use la imagen base de Alpine Linux
FROM alpine:latest

# Establece el trabajo de directorio de trabajo
WORKDIR /root/

# Copia la aplicación construida
COPY --from=builder /app/api-chi .

# Exponga el puerto 8080
EXPOSE 8080

# Ejecuta la aplicación
CMD ["./api-chi"]
