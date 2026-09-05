#!/bin/sh
# Extend the existing guard; keep all vulnerable networks without host/Internet access.
set -eu
iptables -N OUTSIDERS-GUARD 2>/dev/null || true
iptables -C DOCKER-USER -j OUTSIDERS-GUARD 2>/dev/null || iptables -I DOCKER-USER 1 -j OUTSIDERS-GUARD
iptables -F OUTSIDERS-GUARD
iptables -A OUTSIDERS-GUARD -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
for subnet in 172.31.1.0/24 172.31.2.0/24 172.31.3.0/24; do
  iptables -A OUTSIDERS-GUARD -s "$subnet" -d "$subnet" -j RETURN
  iptables -A OUTSIDERS-GUARD -s "$subnet" -j REJECT
done
iptables -A OUTSIDERS-GUARD -j RETURN
# Only the trusted learning container may reach the authenticated host broker.
learning_id=$(docker ps -q --filter label=com.docker.compose.service=learning --filter label=com.docker.compose.project=software-security-internal-labs)
[ -n "$learning_id" ]
learning_ip=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$learning_id")
case "$learning_ip" in 172.30.1.*) ;; *) echo 'Unexpected learning network' >&2; exit 1;; esac
iptables -N OUTSIDERS-HOST 2>/dev/null || true
iptables -C INPUT -j OUTSIDERS-HOST 2>/dev/null || iptables -I INPUT 1 -j OUTSIDERS-HOST
iptables -F OUTSIDERS-HOST
iptables -A OUTSIDERS-HOST -s "$learning_ip/32" -d 172.30.1.1/32 -p tcp --dport 8787 -j ACCEPT
iptables -A OUTSIDERS-HOST -p tcp --dport 8787 -j REJECT
iptables -A OUTSIDERS-HOST -s 172.31.0.0/16 -m conntrack --ctstate NEW -j REJECT
iptables -A OUTSIDERS-HOST -j RETURN
