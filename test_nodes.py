#!/usr/bin/env python3

import requests
import base64
import os
import time


OUTPUT="nodes_all.txt"


SOURCES=[

    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",

    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",

    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/sub.txt"

]


HEADERS={

    "User-Agent":
    "Mozilla/5.0"

}



def decode_base64(text):

    try:

        text=text.strip()

        text=text.replace(
            "\n",
            ""
        )


        text += "=" * (
            4-len(text)%4
        )


        data=base64.b64decode(
            text
        ).decode(
            errors="ignore"
        )


        return data


    except:

        return ""





def extract_nodes(text):


    nodes=set()


    for line in text.splitlines():


        line=line.strip()


        if not line:

            continue



        if "://" in line:


            nodes.add(line)



    return nodes






all_nodes=set()



for url in SOURCES:


    try:


        print(
            "获取:",
            url
        )


        r=requests.get(

            url,

            headers=HEADERS,

            timeout=30

        )


        text=r.text



        nodes=extract_nodes(
            text
        )



        if len(nodes)==0:


            text=decode_base64(
                text
            )


            nodes=extract_nodes(
                text
            )



        print(
            "发现:",
            len(nodes)
        )



        all_nodes.update(
            nodes
        )



    except Exception as e:


        print(
            "失败:",
            str(e)
        )





# 最终清理


clean=set()



for n in all_nodes:


    n=n.strip()


    if len(n)<20:

        continue



    if n.startswith(

        (
            "vmess://",
            "vless://",
            "trojan://",
            "ss://",
            "hy2://",
            "hysteria2://"

        )

    ):

        clean.add(n)




print()

print(
    "最终节点:",
    len(clean)
)




with open(

    OUTPUT,

    "w",

    encoding="utf-8"

) as f:


    for n in sorted(clean):

        f.write(
            n+"\n"
        )



print(
    "保存完成"
)
