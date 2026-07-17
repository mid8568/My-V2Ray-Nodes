#!/bin/bash

NODE="$1"

[ -z "$NODE" ] && exit 1

WORK=$(mktemp -d)

CONFIG="$WORK/config.json"

# 节点转换为 sing-box 配置
node2singbox "$NODE" > "$CONFIG" 2>/dev/null || exit 1


# 添加本地代理入口
jq '
.inbounds=[
{
"type":"mixed",
"tag":"proxy",
"listen":"127.0.0.1",
"listen_port":10808
}
]
' "$CONFIG" > "$WORK/new.json"

mv "$WORK/new.json" "$CONFIG"


# 启动 sing-box
./sing-box run \
-c "$CONFIG" \
>/dev/null 2>&1 &

PID=$!


sleep 2


START=$(date +%s%3N)


# 真实代理测试
RESULT=$(timeout 8 curl \
-x socks5h://127.0.0.1:10808 \
-o /dev/null \
-s \
-w "%{http_code}" \
https://www.google.com/generate_204)


END=$(date +%s%3N)


kill $PID 2>/dev/null


TIME=$((END-START))


if [ "$RESULT" = "204" ] || [ "$RESULT" = "200" ]; then
    echo "$TIME|$NODE"
fi


rm -rf "$WORK"
