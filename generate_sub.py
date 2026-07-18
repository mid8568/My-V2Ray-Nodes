#!/usr/bin/env python3

import base64
import json
import os


RESULT="result.txt"


BASE64_OUT="subscribe.txt"

SINGBOX_OUT="sing-box.json"



def read_nodes():


    nodes=[]


    if not os.path.exists(
        RESULT
    ):

        return nodes



    with open(
        RESULT,
        errors="ignore"
    ) as f:


        for line in f:


            line=line.strip()


            if not line:

                continue



            # 兼容测速格式

            if "ms " in line:

                node=line.split(
                    "ms ",
                    1
                )[1]

            else:

                node=line



            nodes.append(node)



    return nodes





# ======================
# base64订阅
# ======================


def make_base64(nodes):


    text="\n".join(
        nodes
    )


    data=base64.b64encode(

        text.encode()

    ).decode()



    with open(
        BASE64_OUT,
        "w"
    ) as f:


        f.write(data)



# ======================
# sing-box
# ======================


def make_singbox(nodes):


    outbounds=[]



    for i,node in enumerate(nodes):


        outbounds.append(

            {

                "tag":
                "node-"+str(i),

                "type":
                "urltest",

                "outbounds":
                []

            }

        )



    config={


        "log":{

            "level":
            "warn"

        },


        "outbounds":
        outbounds


    }



    with open(
        SINGBOX_OUT,
        "w"
    ) as f:


        json.dump(

            config,

            f,

            indent=2

        )





# ======================
# main
# ======================


nodes=read_nodes()


print(
    "生成订阅节点:",
    len(nodes)
)


make_base64(nodes)


make_singbox(nodes)


print(
    "订阅生成完成"
)
