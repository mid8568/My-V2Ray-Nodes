import urllib.request
from datetime import datetime, timedelta

def get_nodes(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8').strip()
    except Exception:
        return None

def main():
    base_url = "https://githubusercontent.com"
    
    # 获取今天和昨天的日期字符串 (例如 20260716)
    today_str = datetime.now().strftime("%Y%m%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    
    # 构造可能的最新文件名顺序（优先尝试今天的第2个更新，再试第1个，最后退回昨天）
    possible_files = [
        f"v{today_str}2",
        f"v{today_str}1",
        f"v{yesterday_str}2",
        f"v{yesterday_str}1"
    ]
    
    content = None
    success_file = ""
    
    # 循环尝试下载，直到成功获取到一个
    for file_name in possible_files:
        target_url = base_url + file_name
        print(f"正在尝试抓取: {target_url}")
        content = get_nodes(target_url)
        if content and len(content) > 100:  # 确保获取到的内容不是空或报错网页
            success_file = file_name
            break
            
    if content:
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"同步成功！当前提取的文件源为: {success_file}")
    else:
        print("同步失败：未能从目标仓库获取到有效节点。")

if __name__ == "__main__":
    main()
