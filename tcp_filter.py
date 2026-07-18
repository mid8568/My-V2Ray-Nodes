#!/usr/bin/env python3

import concurrent.futures
import os
import random


INPUT="nodes_all.txt"
OUTPUT="alive_nodes.txt"


def check(node):

    # 不做TCP检测
    # 直接交给sing-box

    return node



if not os.path.exists(INPUT):

    print("缺少 nodes_all.txt")
    exit(1)



with open(INPUT,errors="ignore") as f:

    nodes=list(
        set(
            x.strip()
            for x in f
            if x.strip()
        )
    )


print(
    "总节点:",
    len(nodes)
)


random.shuffle(nodes)



# 控制数量
# 不要一次测试24万

nodes=nodes[:5000]



with open(
    OUTPUT,
    "w"
) as f:


    for n in nodes:

        f.write(
            n+"\n"
        )


print(
    "送测试:",
    len(nodes)
)
