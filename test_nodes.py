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
import base64

from urllib.parse import urlparse, parse_qs


INPUT="alive_nodes.txt"

OUTPUT="result.txt"

TEST_URLS=[
    "https://www.gstatic.com/generate_204",
    "https://www.google.com/generate_204",
    "https://cp.cloudflare.com/generate_204"
]


write_lock=threading.Lock()


open(
    OUTPUT,
    "w"
).close()



# =====================
# base64
# =====================

def b64decode(x):

    try:

        return base64.urlsafe_b64decode(
            x+"==="
        ).decode(
            errors="ignore"
        )

    except:

        return ""



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

            "encryption":"none",

            "packet_encoding":"xudp"

        }



        security=q.get(
            "security",
            [""]
        )[0]

           flow=q.get(
            "flow",
               [""]
           )[0]


if flow:

    out["flow"]=flow

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


            pbk=q.get(
                "pbk",
                [""]
            )[0]


            if not pbk:

                return None



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

                "public_key":pbk,

                "short_id":
                q.get(
                    "sid",
                    [""]
                )[0]

            }



        network=q.get(
            "type",
            [""]
        )[0]



        if network=="ws":


            out["transport"]={

                "type":"ws",

                "path":
                q.get(
                    "path",
                    ["/"]
                )[0]

            }



        elif network=="grpc":


            out["transport"]={

                "type":"grpc",

                "service_name":
                q.get(
                    "serviceName",
                    [""]
                )[0]

            }



        return out



    except Exception:


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
                    "sni",
                    obj.get(
                        "host",
                        obj["add"]
                    )
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


        if not u.username:

            return None



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





# =====================
# parser
# =====================

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
# sing-box config
# =====================

def make_config(node,port):


    return {


        "log":{

            "level":"error"

        },


        "inbounds":[


            {

                "type":"mixed",

                "listen":
                "127.0.0.1",

                "listen_port":
                port

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





# =====================
# wait sing-box
# =====================

def wait_port(port):


    for _ in range(30):

        try:

            s=socket.socket()

            s.settimeout(1)


            s.connect(
                (
                    "127.0.0.1",
                    port
                )
            )


            s.close()


            return True



        except:


            time.sleep(0.2)



    return False





# =====================
# test node
# =====================

def test_node(node):


    outbound=parse(node)


    if not outbound:

        return



    port=get_port()



    cfg=tempfile.mktemp(
        suffix=".json"
    )


    p=None



    try:


        with open(
            cfg,
            "w"
        ) as f:


            json.dump(
                make_config(
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

            stderr=subprocess.DEVNULL

        )



        if not wait_port(port):

            return




        start=time.time()

        TEST_URL=random.choice(TEST_URLS)

        r=subprocess.run(

            [

                "curl",

                "-4",

                "--connect-timeout",

                "8",

                "--max-time",

                "15",

                "-A",

                "Mozilla/5.0",

                "-x",

                f"socks5h://127.0.0.1:{port}",

                "-s",

                "-o",

                "/dev/null",

                "-w",

                "%{http_code}",

                TEST_URL

            ],


            capture_output=True,

            timeout=20

        )



        delay=int(

            (time.time()-start)
            *
            1000

        )



        code=r.stdout.decode().strip()

        if code=="000":
            return

        if code in (
            "200",
            "204",
            "301",
            "302"
        ) and delay < 8000:

            print(
                "OK",
                delay,
                node[:60]
            )


            with write_lock:


                with open(
                    OUTPUT,
                    "a"
                ) as f:


                    f.write(

                        f"{delay}ms {node}\n"

                    )



    except Exception:


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
# MAIN
# =====================


if not os.path.exists(INPUT):

    print(
        "缺少 alive_nodes.txt"
    )

    exit(1)




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



# 最多测试300个

nodes=nodes[:500]




print(
    "实际测试:",
    len(nodes)
)





with concurrent.futures.ThreadPoolExecutor(

    max_workers=8

) as pool:


    list(

        pool.map(

            test_node,

            nodes

        )

    )






# =====================
# SORT RESULT
# =====================


if os.path.exists(OUTPUT):


    with open(
        OUTPUT,
        errors="ignore"
    ) as f:


        lines=f.readlines()



    try:


        lines.sort(

            key=lambda x:

            int(
                x.split("ms")[0]
            )

        )


    except:


        pass




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



else:


    print(

        "最终可用:0"

    )
