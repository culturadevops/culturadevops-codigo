FROM golang:1.26.10 AS build
WORKDIR /src
COPY main.go /src/
RUN go mod init backend && CGO_ENABLED=0 go build -ldflags='-s -w' -o /backend .
FROM scratch
COPY --from=build /backend /backend
EXPOSE 9000
ENTRYPOINT ["/backend"]
