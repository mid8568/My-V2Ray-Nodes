import urllib.request
import base64
from datetime import datetime, timedelta, timezone

def get_nodes(url):
    try:
        # 伪装浏览器，防止被拦截
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8').strip()
    except Exception as e:
        print(f"请求失败: {url}，原因: {e}")
        return None

def main():
    # 目标作者的基础路径
    base_url = "https://githubusercontent.com"
    
    # 对齐北京时间
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(tz_beijing)
    
    today_str = now_beijing.strftime("%Y%m%d")
    yesterday_str = (now_beijing - timedelta(days=1)).strftime("%Y%m%d")
    
    # 备选文件名列表
    possible_files = [
        f"v{today_str}2",
        f"v{today_str}1",
        f"v{yesterday_str}2",
        f"v{yesterday_str}1"
    ]
    
    raw_content = None
    success_file = ""
    
    for file_name in possible_files:
        target_url = base_url + file_name
        print(f"正在尝试下载: {target_url}")
        raw_content = get_nodes(target_url)
        if raw_content and len(raw_content) > 50: # 只要文件有内容就立即采用
            success_file = file_name
            break
            
    if raw_content:
        print(f"【对齐成功】已成功获取到目标库文件: {success_file}，文件大小: {len(raw_content)} 字符")
        
        # 判断对方的数据是否已经是 Base64 加密串。如果是，则直接保存；如果不是，则帮它转码
        # 绝不进行单行过滤，防止误删有效数据
        try:
            # 尝试解密，如果能解密说明对方给的就是密文，我们直接存
            base64.b64decode(raw_content.encode('utf-8'), validate=True)
            final_output = raw_content
            print("检测到目标源已经是标准的 Base64 加密串，将直接保存。")
        except Exception:
            # 如果解密报错，说明对方给的是明文，我们将其整体转换为标准的 Base64 订阅密文
            final_output = base64.b64encode(raw_content.encode('utf-8')).decode('utf-8')
            print("检测到目标源为明文节点，已自动为您打包为全平台标准 Base64 订阅。")

        # 写入本地存储
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(final_output)
        print("【保存成功】有效数据已写入 nodes.txt！")
    else:
        print("【同步失败】未能从目标仓库抓取到任何数据。")

if __name__ == "__main__":
    main()
