#!/bin/sh
set -euo pipefail

CONFIG_FILE="/etc/tor/torrc"
ENV_FILE="/home/dockeruser/.env"
PREFIX="TOR_"

# Load environment from .env file manually
set -a
. "$ENV_FILE"
set +a

ALLOWED_KEYS="SocksPort ControlPort ExitNodes EntryNodes Log StrictNodes MaxCircuitDirtiness DataDirectory GeoIPFile GeoIPv6File VirtualAddrNetworkIPv4 AutomapHostsOnResolve TransPort DNSPort ClientOnly HashedControlPassword CookieAuthentication"

# Clear previous config
> "$CONFIG_FILE"

for var in $ALLOWED_KEYS; do
    eval value=\${${PREFIX}${var}:-}
    if [ -n "$value" ]; then
        echo "$var $value" >> "$CONFIG_FILE"
    fi
done

exec "$@"