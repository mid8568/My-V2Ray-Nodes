#!/bin/bash

NODE="$1"

HOST=$(echo "$NODE" | grep -oE '[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:[0-9]+' | tail -1)

[ -z "$HOST" ] && exit 1

IP=${HOST%:*}
PORT=${HOST##*:}

START=$(date +%s%3N)

timeout 3 bash -c "echo >/dev/tcp/$IP/$PORT" 2>/dev/null || exit 1

END=$(date +%s%3N)

TIME=$((END-START))

if [ "$TIME" -lt 2000 ]; then
    echo "$TIME|$NODE"
fi
