#!/usr/bin/env python3

import json
import time
import base64
import random
import tempfile
import subprocess
import concurrent.futures

from urllib.parse import urlparse, parse_qs


INPUT = "nodes_all.txt"
OUTPUT = "result.txt"

TEST_URL = "https://www.gstatic.com/generate_204"

PROXY_PORT = 10808


open(OUTPUT, "w").close()



def b64decode(data):

    try:

        return base64.urlsafe_b64decode(
            data + "==="
        ).decode()

    except:

        return ""



# ---------------- VMESS ----------------

def parse_vmess(uri):

    try:

        raw = uri.replace(
            "vmess://",
            ""
        )

        obj=json.loads(
            b64decode(raw)
        )


        out={

            "type":"vmess",

            "tag":"node",

            "server":obj["add"],

            "server_port":int(obj["port"]),

            "uuid":obj["id"],

            "security":obj.get(
                "scy",
                "auto"
            )

        }


        if obj.get("net")=="ws":

            out["transport"]={

                "type":"ws",

                "path":obj.get(
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


    except Exception:

        return None




# ---------------- VLESS ----------------


def parse_vless(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(u.query)


        out={

            "type":"vless",

            "tag":"node",

            "server":u.hostname,

            "server_port":u.port,

            "uuid":u.username

        }



        flow=q.get(
            "flow",
            [""]
        )[0]


        if flow:

            out["flow"]=flow



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
                    [u.hostname]
                )[0]

            }



        if security=="reality":


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



    except Exception:

        return None




# ---------------- Trojan ----------------


def parse_trojan(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        return {


            "type":"trojan",

            "tag":"node",

            "server":u.hostname,

            "server_port":u.port,

            "password":u.username,


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




# ---------------- SS ----------------


def parse_ss(uri):

    try:

        data=uri[5:]

        data=data.split("#")[0]


        if "@" not in data:

            return None



        user,host=data.rsplit(
            "@",
            1
        )


        raw=b64decode(user)


        method,password=raw.split(
            ":",
            1
        )


        server,port=host.split(
            ":"
        )



        return {


            "type":"shadowsocks",

            "tag":"node",

            "server":server,

            "server_port":int(port),

            "method":method,

            "password":password

        }


    except:

        return None




# ---------------- HY2 ----------------


def parse_hy2(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(
            u.query
        )


        return {


            "type":"hysteria2",

            "tag":"node",

            "server":u.hostname,

            "server_port":u.port,

            "password":u.username,


            "tls":{

                "enabled":True,

                "insecure":True,

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


    if uri.startswith("vmess://"):

        return parse_vmess(uri)


    if uri.startswith("vless://"):

        return parse_vless(uri)


    if uri.startswith("trojan://"):

        return parse_trojan(uri)


    if uri.startswith("ss://"):

        return parse_ss(uri)


    if uri.startswith("hysteria2://"):

        return parse_hy2(uri)


    return None




# ---------------- sing-box config ----------------


def make_config(out):


    return {


        "log":{

            "level":"error"

        },


        "inbounds":[

            {

                "type":"mixed",

                "listen":"127.0.0.1",

                "listen_port":PROXY_PORT

            }

        ],


        "outbounds":[

            out,

            {

                "type":"direct"

            }

        ]

    }




# ---------------- TEST ----------------


def test_node(uri):


    outbound=parse(uri)


    if not outbound:

        return



    path=tempfile.mktemp(
        suffix=".json"
    )


    with open(path,"w") as f:

        json.dump(
            make_config(outbound),
            f
        )


    p=None


    try:


        p=subprocess.Popen(

            [

                "./sing-box",

                "run",

                "-c",

                path

            ],

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL

        )


        time.sleep(1.5)



        start=time.time()


        r=subprocess.run(

            [

                "curl",

                "-A",

                "Mozilla/5.0",

                "-x",

                f"socks5h://127.0.0.1:{PROXY_PORT}",

                "-s",

                "-o",

                "/dev/null",

                "-w",

                "%{http_code}",

                TEST_URL

            ],

            timeout=8,

            capture_output=True

        )


        delay=int(
            (time.time()-start)*1000
        )



        if r.stdout.decode()=="204":


            print(
                "OK",
                delay,
                uri[:40]
            )


            with open(
                OUTPUT,
                "a"
            ) as f:

                f.write(
                    f"{delay}ms {uri}\n"
                )


    except Exception:

        pass


    finally:


        if p:

            p.kill()




# ---------------- MAIN ----------------


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



random.shuffle(nodes)


nodes=nodes[:300]



print(
    "测试节点:",
    len(nodes)
)



with concurrent.futures.ThreadPoolExecutor(

    max_workers=10

) as pool:


    list(
        pool.map(
            test_node,
            nodes
        )
    )



print(
    "测速完成"
)
