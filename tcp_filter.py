#!/usr/bin/env python3

import os


INPUT = "nodes_all.txt"
OUTPUT = "alive_nodes.txt"


if not os.path.exists(INPUT):
    print("缺少 nodes_all.txt")
    exit(1)


with open(INPUT, errors="ignore") as f:
    raw_nodes = [
        x.strip()
        for x in f
        if x.strip()
    ]


# 支持全部协议
protocols = (
    "vless://",
    "vmess://",
    "trojan://",
    "ss://",
    "hy2://",
    "hysteria2://"
)


nodes = []
seen = set()


for n in raw_nodes:

    if n.startswith(protocols):

        if n not in seen:
            seen.add(n)
            nodes.append(n)


print(
    f"原始抓取总数: {len(raw_nodes)}"
)

print(
    f"保留协议节点: {len(nodes)}"
)


with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    for n in nodes:
        f.write(n + "\n")


print(
    "已生成 alive_nodes.txt"
)
