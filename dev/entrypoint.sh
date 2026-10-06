#!/bin/sh
# Copy the pinned HACS build into the config volume, then start Home Assistant.
# A volume mounted on /config hides files that were copied into the image.
set -eu
if [ ! -f /config/custom_components/hacs/manifest.json ]; then
  mkdir -p /config/custom_components/hacs
  cp -a /opt/hacs/. /config/custom_components/hacs/
fi
exec /init
