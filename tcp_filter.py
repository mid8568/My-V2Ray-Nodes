#!/usr/bin/env python3
import os
import random

INPUT = "nodes_all.txt"
OUTPUT = "alive_nodes.txt"
# 添加黑名单，直接从源头过滤已知诱饵
BLACKLIST = ["rooster465.autos", "gossipglove.com", "ignitelimit.com"]

if not os.path.exists(INPUT):
    print("缺少 nodes_all.txt")
    exit(1)

with open(INPUT, errors="ignore") as f:
    raw_nodes = [x.strip() for x in f if x.strip()]

# 剔除黑名单节点并去重
nodes = []
for n in set(raw_nodes):
    if not any(b in n for b in BLACKLIST):
        nodes.append(n)

print(f"原始抓取: {len(raw_nodes)} | 过滤后: {len(nodes)}")

random.shuffle(nodes)
# 控制在 15000 个，减少测速开销
nodes = nodes[:15000]

with open(OUTPUT, "w") as f:
    for n in nodes:
        f.write(n + "\n")

print(f"送入测试: {len(nodes)}")
