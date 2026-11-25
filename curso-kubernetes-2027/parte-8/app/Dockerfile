# k8s-b-api:1 — app del banco (partes 7 y 8 del curso de Kubernetes 2027)
FROM golang:1.26.10 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /api .

FROM alpine:3.24.3
RUN adduser -D -u 10001 app
COPY --from=build /api /api
USER 10001
EXPOSE 8080
ENTRYPOINT ["/api"]
