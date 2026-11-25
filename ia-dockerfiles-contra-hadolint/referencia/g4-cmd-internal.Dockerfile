FROM golang:1.24.11 AS build
WORKDIR /src
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /servidor ./cmd/servidor

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /servidor /servidor
EXPOSE 8080
ENTRYPOINT ["/servidor"]
