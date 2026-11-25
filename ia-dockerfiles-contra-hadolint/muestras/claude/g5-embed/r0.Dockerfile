# syntax=docker/dockerfile:1

FROM golang:1.24-alpine AS build
WORKDIR /src

COPY go.mod ./
RUN go mod download

COPY main.go ./
COPY static ./static

RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/web .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/web /web
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/web"]
