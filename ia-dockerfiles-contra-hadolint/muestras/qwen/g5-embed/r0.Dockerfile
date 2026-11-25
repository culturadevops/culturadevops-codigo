# Use una imagen base de Go
FROM golang:1.24 AS builder

# Copia el archivo go.mod y ejecuta mod tidy
COPY go.mod go.sum ./
RUN go mod download

# Copia el resto de los archivos del proyecto
COPY . .

# Construye la aplicación
RUN go build -o web .

# Use una imagen base de Alpine Linux para la versión de producción
FROM alpine:latest

# Copia la aplicación compilada desde el paso de construcción
COPY --from=builder /go/src/ejemplo.com/web/web /app/web

# Establece el directorio de trabajo
WORKDIR /app

# Exponga el puerto 8080
EXPOSE 8080

# Ejecuta la aplicación
CMD ["./web"]
