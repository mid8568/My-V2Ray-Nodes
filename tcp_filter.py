#!/usr/bin/env python3

import socket
import concurrent.futures
import random
import os


INPUT="nodes_all.txt"

OUTPUT="alive_nodes.txt"


lock=None



def get_host_port(node):

    try:

        from urllib.parse import urlparse

        if node.startswith("vmess://"):

            return None


        u=urlparse(node)


        host=u.hostname

        port=u.port


        if host and port:

            return host,port


    except:

        pass


    return None




def check(node):

    hp=get_host_port(node)


    if not hp:

        return None


    host,port=hp


    try:

        s=socket.socket()

        s.settimeout(2)


        s.connect(
            (
                host,
                port
            )
        )


        s.close()


        return node


    except:

        return None





if not os.path.exists(INPUT):

    print(
        "缺少 nodes_all.txt"
    )

    exit()



with open(
    INPUT,
    errors="ignore"
) as f:


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



alive=[]



with concurrent.futures.ThreadPoolExecutor(

    max_workers=300

) as pool:


    for r in pool.map(
        check,
        nodes
    ):


        if r:

            alive.append(r)


            print(
                "OPEN",
                len(alive),
                r[:60]
            )




with open(
    OUTPUT,
    "w"
) as f:


    for x in alive:

        f.write(
            x+"\n"
        )



print()

print(
    "存活节点:",
    len(alive)
)
