#!/usr/bin/env python3

import os
import json
import time
import base64
import random
import tempfile
import subprocess
import concurrent.futures
from urllib.parse import urlparse, parse_qs, unquote


INPUT="nodes_all.txt"
OUTPUT="result.txt"

TEST_URL="https://www.gstatic.com/generate_204"

PROXY_PORT=10808


open(OUTPUT,"w").close()



def b64decode(data):

    try:
        return base64.urlsafe_b64decode(
            data+"==="
        ).decode()

    except:
        return ""



def parse_vmess(uri):

    try:

        data=uri.replace(
            "vmess://",
            ""
        )

        obj=json.loads(
            b64decode(data)
        )


        outbound={

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


        add_transport(
            outbound,
            obj
        )

        return outbound


    except:

        return None



def add_transport(out,obj):

    net=obj.get(
        "net",
        ""
    )


    if net=="ws":

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
                obj.get("host","")
            )

        }



def parse_vless(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(u.query)


       out={

           "type":"vless",

           "tag":"node",

           "server":u.hostname,

           "server_port":u.port,

           "uuid":u.username,

           "flow":
           q.get(
               "flow",
               [""]
          )[0],

          "packet_encoding":
          "xudp"

}


        if out["flow"] is None:
            del out["flow"]



        security=q.get(
            "security",
            [""]
        )[0]


        if security=="tls" or security=="reality":


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


    except:

        return None




def parse_trojan(uri):

    try:

        u=urlparse(uri)

        q=parse_qs(u.query)


        out={

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


        return out


    except:

        return None




def parse_ss(uri):

    try:


        data=uri[5:]

        data=data.split("#")[0]


        if "@" in data:


            user,host=data.rsplit("@",1)

            raw=b64decode(user)


        else:

            raw=b64decode(data)

            host=""


        if ":" not in raw:
            return None


        method,password=raw.split(
            ":",
            1
        )


        if not host:
            return None


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



def parse_hy2(uri):

    try:

        u=urlparse(uri)
        q=parse_qs(u.query)

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
        "hysteria2://"
    ):
        return parse_hy2(uri)


    return None




def config(out):


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
            PROXY_PORT

            }

        ],


        "outbounds":[

            out,

            {

            "type":"direct"

            }

        ]

    }




def test(uri):


    out=parse(uri)


    if not out:

        return



    tmp=tempfile.mkdtemp()

    cfg=tmp+"/config.json"


    with open(cfg,"w") as f:

        json.dump(
            config(out),
            f
        )


    p=None


    try:


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


        time.sleep(2)


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

            timeout=6,

            capture_output=True

        )


        ms=int(
            (time.time()-start)*1000
        )


        if r.stdout.decode()=="204":


            print(
                "OK",
                ms
            )


            with open(
                OUTPUT,
                "a"
            ) as f:

                f.write(
                    f"{ms}ms {uri}\n"
                )


  except Exception as e:

      print("FAIL",uri[:50],e)


      finally:

          if p:

              p.kill()



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


nodes=nodes[:50]

from collections import Counter

print(
Counter(
x.split("://")[0]
for x in nodes
)
)
print(
    "测试节点:",
    len(nodes)
)


with concurrent.futures.ThreadPoolExecutor(
    max_workers=10
) as ex:


    list(
        ex.map(
            test,
            nodes
        )
    )


print("完成")
