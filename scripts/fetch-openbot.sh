#!/bin/sh
# Ambil OpenBot pada commit yang dipin (versions.env) ke vendor/openbot sebagai konteks build agent-computer.
set -eu
cd "$(dirname "$0")/.."
. ./versions.env
if [ ! -d vendor/openbot/.git ]; then
  mkdir -p vendor && git clone --filter=blob:none --no-checkout "$OPENBOT_REPO" vendor/openbot
fi
git -C vendor/openbot fetch --depth 1 origin "$OPENBOT_REF"
git -C vendor/openbot checkout -q --detach FETCH_HEAD
test "$(git -C vendor/openbot rev-parse HEAD)" = "$OPENBOT_REF" && echo "OpenBot @ $OPENBOT_REF"
