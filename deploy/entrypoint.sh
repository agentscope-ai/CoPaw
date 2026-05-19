#!/bin/sh
# Substitute QWENPAW_PORT in supervisord template and start supervisord.
# Default port 8088; override at runtime with -e QWENPAW_PORT=3000.
set -e

# Auto-initialize if config.json is missing (bind mount with empty directory).
# Set QWENPAW_REQUIRED_INITIALIZATION=0 to skip (e.g. during image warm-up).
if [ "${QWENPAW_REQUIRED_INITIALIZATION:-1}" = "1" ]; then
  if [ ! -f "${QWENPAW_WORKING_DIR}/config.json" ]; then
    qwenpaw init --defaults --accept-security
  fi
else
  echo "Skipping initialization."
fi

export QWENPAW_PORT="${QWENPAW_PORT:-8088}"
envsubst '${QWENPAW_PORT}' \
  < /etc/supervisor/conf.d/supervisord.conf.template \
  > /etc/supervisor/conf.d/supervisord.conf
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf