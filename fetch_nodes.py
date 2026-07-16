import urllib.request
import base64
from datetime import datetime, timedelta, timezone

def get_nodes(url):
    try:
        # 伪装浏览器请求，防止被 GitHub 拦截
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"请求失败的链接: {url}，原因: {e}")
        return None

def check_and_filter_nodes(raw_content):
    """
    检查并过滤出格式合法的有效节点，剔除垃圾文本与广告
    """
    valid_protocols = ('vmess://', 'vless://', 'ss://', 'ssr://', 'trojan://', 'shadowsocks://')
    filtered_nodes = []
    
    lines = raw_content.splitlines()
    for line in lines:
        line = line.strip()
        # 验证是否以合法代理协议开头，且长度合理（防止损坏节点）
        if line.startswith(valid_protocols) and len(line) > 30:
            filtered_nodes.append(line)
                
    return filtered_nodes

def main():
    # 目标作者 free-nodes/v2rayfree 的原始文件基础路径
    base_url = "https://githubusercontent.com"
    
    # 强制锁定东八区（北京时间），完美解决 GitHub 位于美国的服务器时区慢 8 小时的问题
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(tz_beijing)
    
    today_str = now_beijing.strftime("%Y%m%d")
    yesterday_str = (now_beijing - timedelta(days=1)).strftime("%Y%m%d")
    
    # 智能构造由于对方早晚更新导致可能出现的文件名优先级列表
    possible_files = [
        f"v{today_str}2",
        f"v{today_str}1",
        f"v{yesterday_str}2",
        f"v{yesterday_str}1"
    ]
    
    raw_content = None
    success_file = ""
    
    # 循环对齐目标库的文件，直到成功抓取到一个最新的有效文件
    for file_name in possible_files:
        target_url = base_url + file_name
        print(f"正在尝试连接目标库文件: {target_url}")
        raw_content = get_nodes(target_url)
        if raw_content and len(raw_content) > 100:
            success_file = file_name
            break
            
    if raw_content:
        # 开始清洗与安全性筛选
        valid_nodes_list = check_and_filter_nodes(raw_content)
        print(f"【对齐成功】从目标库的 {success_file} 中成功筛选出 {len(valid_nodes_list)} 个有效节点。")
        
        if not valid_nodes_list:
            print("【中断】筛选后的有效节点数量为0，为保护本地旧订阅，本次不写入任何文件。")
            return

        # 把有效节点重新用换行符拼接
        cleaned_plaintext = "\n".join(valid_nodes_list)
        
        # 转换为全球通用的标准 Base64 密文格式（各客户端均能完美识别）
        base64_encoded = base64.b64encode(cleaned_plaintext.encode('utf-8')).decode('utf-8')
        
        # 写入本地存储
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(base64_encoded)
        print("【大功告成】加密后的有效节点已成功保存至 nodes.txt！")
    else:
        print("【极度危险】未能从目标仓库的任何备选链接中获取到数据，请检查网络或目标库结构。")

if __name__ == "__main__":
    main()
