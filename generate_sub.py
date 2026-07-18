#!/usr/bin/env python3

import base64
import json
import os


INPUT="result.txt"

OUTPUT="subscribe.txt"

JSON_OUTPUT="nodes.json"



if not os.path.exists(INPUT):

    print(
        "缺少 result.txt"
    )

    exit(1)



# ==========================
# 读取测速结果
# ==========================


nodes=[]


with open(
    INPUT,
    errors="ignore"
) as f:


    for line in f:


        line=line.strip()


        if not line:

            continue


        try:

import re


    m=re.search(
    r'\d+ms\s+(.*)',
    line
    )


    if m:

    nodes.append(
        m.group(1)
    )

            nodes.append(node)


        except:

            pass



print(
    "有效节点:",
    len(nodes)
)



if len(nodes)==0:

    exit()



# ==========================
# 原始订阅
# ==========================


raw="\n".join(
    nodes
)


encoded=base64.b64encode(

    raw.encode()

).decode()



with open(
    OUTPUT,
    "w"
) as f:


    f.write(
        encoded
    )



print(
    "生成:",
    OUTPUT
)



# ==========================
# sing-box 简易配置
# ==========================


outbounds=[]


for i,node in enumerate(nodes):


    outbounds.append(

        {

        "type":"urltest",

        "tag":
        "node-"+str(i),

        "url":
        "https://www.gstatic.com/generate_204",

        "interval":
        "5m"

        }

    )



config={


"log":{

"level":"error"

},


"outbounds":outbounds



}



with open(
    JSON_OUTPUT,
    "w"
) as f:


    json.dump(

        config,

        f,

        indent=2

    )



print(
    "生成:",
    JSON_OUTPUT
)
