# See caddy.Dockerfile for the security/reproducibility rationale. Keep this
# builder block aligned so BuildKit can share the expensive compile cache.
FROM golang:1.26.6-alpine3.23@sha256:e57c41c1d5864341031181b0db34b9a537bb5773eb6428e4e5bdaea0f9135406 AS caddy-builder
ARG CADDY_SOURCE_COMMIT=e2eee6a7fce366321294c9c2a79f3146891dcbdf
RUN apk add --no-cache ca-certificates git \
    && git clone --depth 1 --branch v2.11.4 https://github.com/caddyserver/caddy.git /src \
    && test "$(git -C /src rev-parse HEAD)" = "$CADDY_SOURCE_COMMIT"
WORKDIR /src
RUN go get golang.org/x/crypto@v0.55.0 \
        golang.org/x/net@v0.57.0 \
        golang.org/x/text@v0.41.0 \
        google.golang.org/grpc@v1.83.1 \
    && go mod tidy \
    && CGO_ENABLED=0 GOMAXPROCS=1 go build -p=1 -trimpath -ldflags='-s -w' -o /out/caddy ./cmd/caddy

FROM alpine:3.23.5@sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40
ENV XDG_CONFIG_HOME=/config XDG_DATA_HOME=/data
RUN apk upgrade --no-cache \
    && apk add --no-cache ca-certificates mailcap \
    && addgroup -S -g 10001 caddy \
    && adduser -S -D -H -u 10001 -G caddy caddy \
    && mkdir -p /data /config /etc/caddy \
    && chown -R 10001:10001 /data /config /etc/caddy
COPY --from=caddy-builder /out/caddy /usr/bin/caddy

COPY --chown=10001:10001 deploy/internal-labs/Relay.Caddyfile /etc/caddy/Caddyfile

USER 10001:10001
EXPOSE 8080
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
