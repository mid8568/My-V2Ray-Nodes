#!/usr/bin/env python3

import base64
import os


INPUT="nodes.txt"


OUTPUT="base64.txt"


if not os.path.exists(INPUT):

    print("没有 nodes.txt")

    exit(1)



with open(
    INPUT,
    "r",
    encoding="utf-8",
    errors="ignore"
) as f:

    nodes=[
        x.strip()
        for x in f
        if x.strip()
    ]



if len(nodes)==0:

    print("有效节点:0")

    exit(1)



data="\n".join(nodes)



encoded=base64.b64encode(
    data.encode()
).decode()



with open(
    OUTPUT,
    "w"
) as f:

    f.write(encoded)



print(
    "有效节点:",
    len(nodes)
)


print(
    "生成:",
    OUTPUT
)
