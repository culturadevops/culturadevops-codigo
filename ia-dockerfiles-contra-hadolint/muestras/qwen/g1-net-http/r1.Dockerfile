# Use la imagen base de Go
FROM golang:1.24 AS builder

# Establece el trabajo de directorio de trabajo
WORKDIR /app

# Copia el archivo go.mod y ejecuta mod tidy
COPY go.mod .
RUN go mod download

# Copia el código fuente y compila la aplicación
COPY . .
RUN go build -o servidor .

# Crea una nueva imagen de producción
FROM alpine:3.19

# Establece el trabajo de directorio de trabajo
WORKDIR /root/

# Copia la aplicación compilada desde la imagen de construcción
COPY --from=builder /app/servidor .

# Exponga el puerto 8080
EXPOSE 8080

# Ejecuta la aplicación
CMD ["./servidor"]
