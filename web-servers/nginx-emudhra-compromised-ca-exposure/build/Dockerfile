FROM golang:1.27.3-alpine@sha256:d200d2dd76b03a99b52651fd1325aff7dcd35422c35c01bac56571b0507f3deb AS build
WORKDIR /src
ENV CGO_ENABLED=0
COPY go.mod tlscheck.go ./
RUN go build -trimpath -ldflags="-s -w" -o /out/tlscheck ./tlscheck.go

FROM nginx:1.25-alpine@sha256:516475cc129da42866742567714ddc681e5eed7b9ee0b9e9c015e464b4221a00
COPY --from=build /out/tlscheck /app/tlscheck
COPY certs/ /app/certs/
COPY default.conf /etc/nginx/conf.d/default.conf
RUN chmod 0644 /app/certs/*.pem
EXPOSE 443
