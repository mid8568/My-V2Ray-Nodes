import urllib.request
import base64
from datetime import datetime, timedelta, timezone

def get_nodes(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"尝试请求失败: {url}，原因: {e}")
        return None

def check_and_filter_nodes(raw_content):
    """
    检查并筛选出格式合法的有效节点，剔除网页垃圾代码或广告文本
    """
    valid_protocols = ('vmess://', 'vless://', 'ss://', 'ssr://', 'trojan://', 'shadowsocks://')
    filtered_nodes = []
    
    # 按行切割内容并逐行检查
    lines = raw_content.splitlines()
    for line in lines:
        line = line.strip()
        # 1. 检查是否以主流代理协议开头
        if line.startswith(valid_protocols):
            # 2. 过滤掉过短的损坏节点
            if len(line) > 30:
                filtered_nodes.append(line)
                
    return filtered_nodes

def main():
    # 目标仓库的原始数据基础链接
    base_url = "https://githubusercontent.com"
    
    # 强制使用东八区（北京时间）防止时区算错日期
    tz_beijing = timezone(timedelta(hours=8))
    now_beijing = datetime.now(tz_beijing)
    
    today_str = now_beijing.strftime("%Y%m%d")
    yesterday_str = (now_beijing - timedelta(days=1)).strftime("%Y%m%d")
    
    # 构造匹配优先级
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
        print(f"正在检查目标文件: {target_url}")
        raw_content = get_nodes(target_url)
        if raw_content and len(raw_content) > 100:
            success_file = file_name
            break
            
    if raw_content:
        # 执行节点清洗与有效性检查
        valid_nodes_list = check_and_filter_nodes(raw_content)
        print(f"【检查完毕】源文件 {success_file} 总计包含 {len(lines) if 'lines' in locals() else '未知'} 行数据。")
        print(f"【筛选结果】成功提取出 {len(valid_nodes_list)} 个格式合法的有效节点！")
        
        if not valid_nodes_list:
            print("【警告】未筛选到任何合法的节点链接，本次不写入文件。")
            return

        # 将筛选后的标准明文节点合并
        cleaned_plaintext = "\n".join(valid_nodes_list)
        
        # 转换成全平台客户端最通用的 Base64 订阅标准加密串
        # 这样你的订阅链接在任何老旧客户端上点击“更新”都不会报编码错误
        base64_encoded = base64.b64encode(cleaned_plaintext.encode('utf-8')).decode('utf-8')
        
        # 写入到你的本地 nodes.txt 文件中
        with open("nodes.txt", "w", encoding="utf-8") as f:
            f.write(base64_encoded)
        print("【同步成功】经过清洗与 Base64 编码的有效节点已成功写入 nodes.txt！")
    else:
        print("【错误】未能从目标仓库抓取到有效内容。")

if __name__ == "__main__":
    main()
