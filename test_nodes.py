def parse_node(node):

    try:

        if node.startswith("vless://"):

            u = urllib.parse.urlparse(node)

            return {

                "type": "vless",

                "tag": "proxy",

                "server": u.hostname,

                "server_port": u.port,

                "uuid": u.username,

                "tls": {
                    "enabled": True,
                    "server_name": u.hostname
                }
            }


        elif node.startswith("vmess://"):

            raw = node[8:]


            # 新格式:
            # vmess://uuid@host:port?参数
            if "@" in raw:


                u = urllib.parse.urlparse(node)

                params = urllib.parse.parse_qs(
                    u.query
                )


                return {

                    "type": "vmess",

                    "tag": "proxy",

                    "server": u.hostname,

                    "server_port": u.port,

                    "uuid": u.username,

                    "security": params.get(
                        "encryption",
                        ["auto"]
                    )[0],

                    "tls": {
                        "enabled":
                        params.get(
                            "security",
                            ["none"]
                        )[0] == "tls"
                    }
                }


            # 老格式:
            # vmess://base64(json)

            decoded = base64.b64decode(
                raw + "==="
            ).decode(
                errors="ignore"
            )


            obj = json.loads(decoded)


            return {

                "type": "vmess",

                "tag": "proxy",

                "server": obj["add"],

                "server_port": int(
                    obj["port"]
                ),

                "uuid": obj["id"],

                "security": obj.get(
                    "scy",
                    "auto"
                ),

                "tls": {
                    "enabled":
                    obj.get(
                        "tls",
                        ""
                    ) == "tls"
                }
            }


    except Exception as e:

        return None
