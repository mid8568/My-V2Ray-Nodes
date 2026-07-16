import urllib.request
import base64
import os
from datetime import datetime

def fetch_and_save():
    # 目标节点的原始链接
    url = "https://githubusercontent.com"
    
    try:
        # 发送请求获取节点数据
        print(f"正在从目标链接获取节点...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8').strip()
        
        # 简单验证获取到的内容是否为空
        if not content:
            print("错误：获取到的节点内容为空！")
            return
            
        # 将获取到的节点写入到你的 nodes.txt 文件中
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("成功：节点已成功同步到 nodes.txt 文件！")
            
    except Exception as e:
        print(f"同步失败，错误原因: {e}")

if __name__ == "__main__":
    fetch_and_save()
