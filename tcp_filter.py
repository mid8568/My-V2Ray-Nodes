#!/usr/bin/env python3

import os
import random

INPUT = "nodes_all.txt"
OUTPUT = "alive_nodes.txt"

if not os.path.exists(INPUT):
    print("缺少 nodes_all.txt")
    exit(1)

with open(INPUT, errors="ignore") as f:
    nodes = list(
        set(
            x.strip()
            for x in f
            if x.strip()
        )
    )

print("抓取到的总节点数:", len(nodes))

# 随机打乱
random.shuffle(nodes)

# 扩大筛选池，从海量节点中随机抽取 30000 个送去深度测速
nodes = nodes[:30000]

with open(OUTPUT, "w") as f:
    for n in nodes:
        f.write(n + "\n")

print("送入下一步测速的节点数:", len(nodes))
