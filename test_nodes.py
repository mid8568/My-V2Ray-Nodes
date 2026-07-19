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


print("原始节点:", len(raw_nodes))
print("保留节点:", len(nodes))


with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:
    for n in nodes:
        f.write(n + "\n")


print("生成 alive_nodes.txt")
