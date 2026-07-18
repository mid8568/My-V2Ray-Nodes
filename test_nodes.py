#!/usr/bin/env python3

import json
import time
import random
import tempfile
import subprocess
import concurrent.futures
import os
import threading
import socket

from urllib.parse import urlparse, parse_qs
import base64


INPUT="alive_nodes.txt"

OUTPUT="result.txt"

TEST_URL="https://www.gstatic.com/generate_204"


write_lock=threading.Lock()



open(
    OUTPUT,
    "w"
).close()



# =====================
# port
# =====================

def get_port():

    s=socket.socket()

    s.bind(
        (
            "127.0.0.1",
            0
        )
    )

    port=s.getsockname()[1]

    s.close()

    return port



# =====================
# base64
# =====================

def b64decode(x):

    try:

        return base64.urlsafe_b64decode(
            x+"==="
        ).decode()

    except:

        return ""



# =====================
# VLESS
# =====================

def parse_vless(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        host=u.hostname


        if not host:

            return None



        out={

            "type":"vless",

            "tag":"proxy",

            "server":host,

            "server_port":u.port,

            "uuid":u.username,

            "encryption":"none"

        }



        security=q.get(
            "security",
            [""]
        )[0]



        if security in (
            "tls",
            "reality"
        ):


            out["tls"]={

                "enabled":True,

                "server_name":
                q.get(
                    "sni",
                    [host]
                )[0]

            }



        if security=="reality":


            out["tls"]["utls"]={

                "enabled":True,

                "fingerprint":
                q.get(
                    "fp",
                    ["chrome"]
                )[0]

            }



            out["tls"]["reality"]={

                "enabled":True,

                "public_key":
                q.get(
                    "pbk",
                    [""]
                )[0],

                "short_id":
                q.get(
                    "sid",
                    [""]
                )[0]

            }



        net=q.get(
            "type",
            [""]
        )[0]


        if net=="ws":


            out["transport"]={

                "type":"ws",

                "path":
                q.get(
                    "path",
                    ["/"]
                )[0]

            }


        elif net=="grpc":


            out["transport"]={

                "type":"grpc",

                "service_name":
                q.get(
                    "serviceName",
                    [""]
                )[0]

            }



        return out



    except:

        return None





# =====================
# VMESS
# =====================

def parse_vmess(uri):

    try:


        raw=uri.replace(
            "vmess://",
            ""
        )


        obj=json.loads(
            b64decode(raw)
        )


        out={

            "type":"vmess",

            "tag":"proxy",

            "server":
            obj["add"],

            "server_port":
            int(obj["port"]),

            "uuid":
            obj["id"],

            "security":
            obj.get(
                "scy",
                "auto"
            )

        }


        if obj.get("net")=="ws":


            out["transport"]={

                "type":"ws",

                "path":
                obj.get(
                    "path",
                    "/"
                )

            }


        if obj.get("tls")=="tls":


            out["tls"]={

                "enabled":True,

                "server_name":
                obj.get(
                    "host",
                    obj["add"]
                )

            }



        return out


    except:

        return None




# =====================
# Trojan
# =====================


def parse_trojan(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        return {


            "type":"trojan",

            "tag":"proxy",

            "server":
            u.hostname,

            "server_port":
            u.port,

            "password":
            u.username,


            "tls":{

                "enabled":True,

                "server_name":
                q.get(
                    "sni",
                    [u.hostname]
                )[0]

            }


        }


    except:

        return None





def parse(uri):


    if uri.startswith(
        "vless://"
    ):

        return parse_vless(uri)


    if uri.startswith(
        "vmess://"
    ):

        return parse_vmess(uri)


    if uri.startswith(
        "trojan://"
    ):

        return parse_trojan(uri)


    return None





# =====================
# config
# =====================


def config(node,port):


    return {


        "log":{

            "level":"error"

        },


        "inbounds":[

            {

            "type":"mixed",

            "listen":"127.0.0.1",

            "listen_port":port

            }

        ],


        "outbounds":[

            node,

            {

            "type":"direct",

            "tag":"direct"

            }

        ]


    }






def test(node):


    outbound=parse(node)


    if not outbound:

        return



    port=get_port()


    cfg=tempfile.mktemp(
        ".json"
    )


    p=None



    try:


        with open(
            cfg,
            "w"
        ) as f:


            json.dump(
                config(
                    outbound,
                    port
                ),
                f
            )



        p=subprocess.Popen(

            [

            "./sing-box",

            "run",

            "-c",

             cfg

            ],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.PIPE

        )



        time.sleep(0.5)



        if p.poll()!=None:

            return




        start=time.time()



        r=subprocess.run(

            [

            "curl",

            "-4",

            "--connect-timeout",
            "5",

            "--max-time",
            "8",

            "-x",

            f"socks5h://127.0.0.1:{port}",

            "-s",

            "-o",

            "/dev/null",

            "-w",

            "%{{http_code}}",

            TEST_URL

            ],

            capture_output=True,

            timeout=10

        )



        delay=int(
            (time.time()-start)*1000
        )



        code=r.stdout.decode()



        if code in (

                "200",
                "204",
                "301",
                "302"

          ):


            print(
                "OK",
                delay
            )


            with write_lock:


                with open(
                    OUTPUT,
                    "a"
                ) as f:


                    f.write(
                        f"{delay}ms {node}\n"
                    )


    except:

        pass


    finally:


        try:

            if p:

                p.kill()

        except:

            pass


        try:

            os.remove(cfg)

        except:

            pass







# =====================
# main
# =====================


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
    "待测试:",
    len(nodes)
)



random.shuffle(nodes)



# 最多测试5000

nodes=nodes[:5000]



with concurrent.futures.ThreadPoolExecutor(

    max_workers=30

) as pool:


    list(
        pool.map(
            test,
            nodes
        )
    )





with open(
    OUTPUT
) as f:

    lines=f.readlines()



lines.sort(
    key=lambda x:
    int(x.split("ms")[0])
)



with open(
    OUTPUT,
    "w"
) as f:

    f.writelines(lines)



print()

print(
    "最终可用:",
    len(lines)
)
