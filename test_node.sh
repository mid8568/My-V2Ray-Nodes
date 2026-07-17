#!/bin/bash

NODE="$1"


# 简单协议检查

HOST=$(echo "$NODE" | grep -oE '[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:[0-9]+' | tail -1)


[ -z "$HOST" ] && exit 1


IP=${HOST%:*}
PORT=${HOST##*:}


START=$(date +%s%3N)


timeout 5 bash -c "</dev/tcp/$IP/$PORT" || exit 1


END=$(date +%s%3N)


TIME=$((END-START))


if [ "$TIME" -lt 2000 ]

then

echo "$TIME|$NODE" >> result.txt

fi
