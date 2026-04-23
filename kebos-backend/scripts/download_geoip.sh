#!/bin/bash
# Download GeoLite2-City database (requires free MaxMind account)
# Register at: https://www.maxmind.com/en/geolite2/signup
# Set MAXMIND_LICENSE_KEY in your environment before running this script.
set -e
DEST="kebos-backend/data/GeoLite2-City.mmdb"
mkdir -p kebos-backend/data
if [ -z "$MAXMIND_LICENSE_KEY" ]; then
    echo "ERROR: MAXMIND_LICENSE_KEY not set. Get a free key at maxmind.com"
    exit 1
fi
URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz"
curl -fsSL "$URL" -o /tmp/geoip.tar.gz
tar -xzf /tmp/geoip.tar.gz -C /tmp
cp /tmp/GeoLite2-City_*/GeoLite2-City.mmdb "$DEST"
echo "GeoLite2-City.mmdb installed → $DEST"
