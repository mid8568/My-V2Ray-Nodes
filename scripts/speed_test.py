#!/usr/bin/env python3

import time
import subprocess


INPUT="tcp_alive_nodes.txt"
OUTPUT="speed_rank.txt"


def fake_speed_test(node):

    """
    这里以后替换成真实 sing-box测速
    """

    start=time.time()

    # 模拟检测
    time.sleep(0.1)

    delay=time.time()-start


    # 临时评分
    speed=max(1,int(300/(delay*1000+1)))

    return speed



results=[]


with open(INPUT,"r",encoding="utf-8") as f:

    nodes=f.readlines()


for i,node in enumerate(nodes):

    node=node.strip()

    if not node:
        continue


    print(
        f"测速 {i+1}/{len(nodes)}"
    )


    speed=fake_speed_test(node)


    print(
        speed,
        "Mbps"
    )


    results.append(
        (
            speed,
            node
        )
    )


results.sort(
    reverse=True,
    key=lambda x:x[0]
)


with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:


    for speed,node in results:

        f.write(
            f"{speed}|{node}\n"
        )


print(
    "测速完成:",
    len(results)
)
