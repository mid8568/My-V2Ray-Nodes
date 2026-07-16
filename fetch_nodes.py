import urllib.request
from datetime import datetime, timedelta, timezone

def get_nodes(url):
    try:
        # 使用统一的标头伪装
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8').strip()
    except Exception as e:
        print(f"读取失败: {url}，原因: {e}")
        return None

def main():
    # 💡 终极修复：必须使用 raw.githubusercontent.com 并且包含正确的作者仓库路径和末尾斜杠
    base_url = "https://githubusercontent.com"
    
    # 精准对齐北京时间
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(tz_beijing)
    
    today_str = now_beijing.strftime("%Y%m%d")
    yesterday_str = (now_beijing - timedelta(days=1)).strftime("%Y%m%d")
    
    # 智能匹配目标库文件名（如 v202607162）
    possible_files = [
        f"v{today_str}2",
        f"v{today_str}1",
        f"v{yesterday_str}2",
        f"v{yesterday_str}1"
    ]
    
    content = None
    success_file = ""
    
    for file_name in possible_files:
        target_url = base_url + file_name
        print(f"正在尝试抓取目标链接: {target_url}")
        content = get_nodes(target_url)
        if content and len(content) > 50:
            success_file = file_name
            break
            
    if content:
        # 终极简化：不做任何筛选或 Base64 加密，抓到什么数据，就原封不动写入文件
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"【成功】已成功将 {success_file} 的原始明文节点存入 nodes.txt！")
        print("节点内容前50个字符为：", content[:50])
    else:
        print("【错误】所有链接均未抓取到有效内容。")

if __name__ == "__main__":
    main()
