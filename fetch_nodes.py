import urllib.request
from datetime import datetime, timedelta, timezone

def get_nodes(url):
    try:
        # 使用更真实的浏览器 User-Agent 伪装，避免触发基本的策略拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore').strip()
    except Exception as e:
        print(f"该镜像源请求失败: {url}，原因: {e}")
        return None

def main():
    # 精准对齐北京时间
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(tz_beijing)
    
    today_str = now_beijing.strftime("%Y%m%d")
    yesterday_str = (now_beijing - timedelta(days=1)).strftime("%Y%m%d")
    
    # 智能匹配目标库文件名
    file_names = [
        f"v{today_str}2",
        f"v{today_str}1",
        f"v{yesterday_str}2",
        f"v{yesterday_str}1"
    ]
    
    content = None
    success_file = ""
    
    # ⚡ 终极多重备用镜像源策略，彻底轰开 GitHub 官方的反爬拦截 ⚡
    for file_name in file_names:
        # 构造三个不同的全球 CDN 加速镜像站和官方源
        mirrors = [
            f"https://jsdelivr.net{file_name}", # JSDelivr 镜像（最稳）
            f"https://jsdelivr.net{file_name}", # Fastly 节点
            f"https://githubusercontent.com{file_name}" # 官方源保底
        ]
        
        for url in mirrors:
            print(f"正在通过镜像渠道尝试抓取: {url}")
            content = get_nodes(url)
            if content and len(content) > 100: # 只要数据有效（大于100字符），立刻锁死退出
                success_file = file_name
                break
        if content:
            break
            
    if content:
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"【突破封锁成功】已成功将 {success_file} 的数据存入 nodes.txt，大小为 {len(content)} 字节！")
    else:
        print("【严重错误】所有 CDN 镜像源和官方源均被 GitHub 强行拦截或目标尚未更新！")

if __name__ == "__main__":
    main()
