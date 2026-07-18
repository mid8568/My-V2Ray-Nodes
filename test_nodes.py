#!/usr/bin/env python3

import json
import time
import base64
import random
import tempfile
import subprocess
import concurrent.futures
import os
import threading
import socket

from urllib.parse import urlparse, parse_qs


INPUT="nodes_all.txt"

OUTPUT="result.txt"


TEST_URLS=[
    "https://www.gstatic.com/generate_204",
    "https://www.google.com/generate_204",
    "https://www.cloudflare.com",
    "https://www.youtube.com"
]


write_lock=threading.Lock()


open(
    OUTPUT,
    "w"
).close()



# =========================
# base64
# =========================


def b64decode(data):

    try:

        return base64.urlsafe_b64decode(
            data+"==="
        ).decode(
            errors="ignore"
        )

    except:

        return ""





# =========================
# TCP CHECK
# =========================


def tcp_check(host,port,timeout=3):

    try:

        s=socket.socket()

        s.settimeout(timeout)


        r=s.connect_ex(
            (
                host,
                int(port)
            )
        )


        s.close()


        return r==0


    except:

        return False





# =========================
# RANDOM PORT
# =========================


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





# =========================
# VMESS
# =========================


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


            "alter_id":
            int(
                obj.get(
                    "aid",
                    0
                )
            ),


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






# =========================
# VLESS
# =========================


def parse_vless(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        host=u.hostname


        if not host or not u.port:

            return None



        security=q.get(
            "security",
            [""]
        )[0]



        # Reality必须参数

        if security=="reality":


            if not q.get("pbk"):

                return None


            if not q.get("sni"):

                return None





        out={


            "type":"vless",

            "tag":"proxy",


            "server":host,


            "server_port":u.port,


            "uuid":u.username,


            "encryption":"none"


        }



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


    except:


        return None

# =========================
# TROJAN
# =========================


def parse_trojan(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        host=u.hostname


        if not host or not u.port:

            return None



        return {


            "type":"trojan",

            "tag":"proxy",


            "server":host,


            "server_port":u.port,


            "password":
            u.username,



            "tls":{


                "enabled":True,


                "server_name":
                q.get(
                    "sni",
                    [host]
                )[0],


                "utls":{


                    "enabled":True,


                    "fingerprint":
                    q.get(
                        "fp",
                        ["chrome"]
                    )[0]

                }


            }


        }


    except:


        return None





# =========================
# SHADOWSOCKS
# =========================


def parse_ss(uri):

    try:


        data=uri[5:]


        data=data.split(
            "#"
        )[0]



        if "@" not in data:

            return None



        user,host=data.rsplit(
            "@",
            1
        )



        try:

            user=base64.urlsafe_b64decode(
                user+"==="
            ).decode()


        except:

            pass



        method,password=user.split(
            ":",
            1
        )



        server,port=host.rsplit(
            ":",
            1
        )



        return {


            "type":"shadowsocks",

            "tag":"proxy",


            "server":server,


            "server_port":int(port),


            "method":method,


            "password":password


        }


    except:


        return None






# =========================
# HYSTERIA2
# =========================


def parse_hy2(uri):

    try:


        if uri.startswith(
            "hy2://"
        ):

            uri=uri.replace(
                "hy2://",
                "hysteria2://"
            )



        u=urlparse(uri)


        q=parse_qs(
            u.query
        )


        host=u.hostname


        if not host:

            return None



        return {


            "type":"hysteria2",

            "tag":"proxy",


            "server":host,


            "server_port":
            u.port or 443,


            "password":
            u.username,



            "tls":{


                "enabled":True,


                "insecure":True,


                "server_name":
                q.get(
                    "sni",
                    [host]
                )[0]


            }


        }



    except:


        return None





# =========================
# NODE PARSER
# =========================


def parse(uri):


    if uri.startswith(
        "vmess://"
    ):

        return parse_vmess(uri)



    if uri.startswith(
        "vless://"
    ):

        return parse_vless(uri)



    if uri.startswith(
        "trojan://"
    ):

        return parse_trojan(uri)



    if uri.startswith(
        "ss://"
    ):

        return parse_ss(uri)



    if uri.startswith(
        "hy2://"
    ) or uri.startswith(
        "hysteria2://"
    ):

        return parse_hy2(uri)



    return None






# =========================
# SING-BOX CONFIG
# =========================


def make_config(out,port):


    return {


        "log":{

            "level":"error"

        },



        "dns":{

            "servers":[

                {

                    "tag":"dns",

                    "address":
                    "https://1.1.1.1/dns-query"

                }

            ]

        },



        "inbounds":[


            {


                "type":"mixed",


                "listen":
                "127.0.0.1",


                "listen_port":port


            }


        ],



        "outbounds":[


            out,


            {


                "type":"direct",

                "tag":"direct"

            }


        ]


    }





# =========================
# WAIT PORT
# =========================


def wait_port(port):


    for _ in range(40):


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


            time.sleep(0.25)



    return False






# =========================
# TEST NODE
# =========================


def test_node(uri):


    outbound=parse(uri)



    if not outbound:


        return




    # TCP过滤


    if not tcp_check(

        outbound["server"],

        outbound["server_port"]

    ):


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


            stderr=subprocess.PIPE

        )



        time.sleep(0.5)



        if p.poll() is not None:


            return




        if not wait_port(port):


            return




        url=random.choice(
            TEST_URLS
        )



        start=time.time()



        r=subprocess.run(

            [

                "curl",

                "-4",

                "--connect-timeout",

                "15",

                "--max-time",

                "40",

                "-A",

                "Mozilla/5.0",

                "-x",

                f"socks5h://127.0.0.1:{port}",

                "-s",

                "-o",

                "/dev/null",

                "-w",

                "%{http_code}",

                url

            ],


            capture_output=True,


            timeout=45

        )




        delay=int(

            (time.time()-start)

            *1000

        )



        code=r.stdout.decode().strip()




        if code in (

            "200",

            "204",

            "301",

            "302"

        ):



            print(

                "OK",

                delay,

                uri[:50]

            )



            with write_lock:


                with open(

                    OUTPUT,

                    "a"

                ) as f:


                    f.write(

                        f"{delay}ms {uri}\n"

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

# =========================
# MAIN
# =========================


if not os.path.exists(INPUT):

    print(
        "缺少 nodes_all.txt"
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
    "读取节点:",
    len(nodes)
)




random.shuffle(nodes)



# 测试全部节点

print(
    "开始测试:",
    len(nodes)
)





with concurrent.futures.ThreadPoolExecutor(

    max_workers=30

) as pool:


    list(

        pool.map(

            test_node,

            nodes

        )

    )





# =========================
# SORT RESULT
# =========================


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



print(
    "完成"
)
