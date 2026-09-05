#!/usr/bin/env bash
# Dedicated Linux lab host only. Do not run on a general-purpose Docker host.
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run as root on the dedicated VPN lab host.' >&2; exit 2; }
iptables -nL DOCKER-USER >/dev/null
iptables -N SEMESTER-LAB-GUARD 2>/dev/null || true
iptables -C DOCKER-USER -j SEMESTER-LAB-GUARD 2>/dev/null || iptables -I DOCKER-USER 1 -j SEMESTER-LAB-GUARD
iptables -F SEMESTER-LAB-GUARD
iptables -A SEMESTER-LAB-GUARD -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
for n in 0 1 2 3 4 5 6 7; do
  subnet="172.29.$n.0/24"
  iptables -A SEMESTER-LAB-GUARD -s "$subnet" -d "$subnet" -j RETURN
  iptables -A SEMESTER-LAB-GUARD -s "$subnet" -j REJECT
done
iptables -A SEMESTER-LAB-GUARD -j RETURN
iptables -C INPUT -i 'br+' -m conntrack --ctstate NEW -j REJECT 2>/dev/null || iptables -I INPUT 1 -i 'br+' -m conntrack --ctstate NEW -j REJECT
iptables -C INPUT -i docker0 -m conntrack --ctstate NEW -j REJECT 2>/dev/null || iptables -I INPUT 1 -i docker0 -m conntrack --ctstate NEW -j REJECT
