import os, re, time, requests

def get_asset_id(cid, path):
    url = f"https://www.ofiii.com/{path}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/"
    }
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # 尝试多种可能的匹配模式
            # 模式 1: 原始路径匹配
            match = re.search(r"playlist/([a-zA-Z0-9_-]+)/master\.m3u8", res.text)
            # 模式 2: 如果模式 1 失败，尝试匹配 JSON 数据中的 ID
            if not match:
                match = re.search(r"\"assetId\":\"([a-zA-Z0-9_-]+)\"", res.text)
            
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 成功: {aid}")
                return aid
            else:
                print(f"⚠️ {cid} 页面已打开但未找到 ID (正则失效)")
        else:
            print(f"❌ {cid} 错误: {res.status_code} (路径可能变了)")
    except Exception as e:
        print(f"🔥 {cid} 异常: {str(e)}")
    return None

def sync():
    # 重新梳理后的最新路径映射
    channels = {
        'lhtv01': 'channel/watch/litv-longturn03', # 200 - 正确
        'lhtv02': 'channel/watch/litv-longturn04', # 之前是 404，需尝试新 ID
        'lhtv03': 'channel/watch/litv-longturn02', # 200 - 正确
        'lhtv04': 'channel/watch/litv-longturn01', # 之前是 404
        'lhtv05': 'channel/watch/ofiii73',         # 200 - 正确
        'lhtv06': 'channel/watch/ofiii74',
        'lhtv07': 'channel/watch/ofiii76',
    }
    
    if not os.path.exists("workers.js"): return

    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, path in channels.items():
        aid = get_asset_id(cid, path)
        if aid:
            # 兼容不同格式的替换
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(1)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 同步成功！")

if __name__ == "__main__":
    sync()
