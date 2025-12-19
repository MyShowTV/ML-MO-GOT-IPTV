import os, re, time, requests

def get_asset_id(cid, slug):
    url = f"https://www.ofiii.com/channel/watch/{slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # 方案 1：暴力搜索所有 assetId 关键字后面的字符串
            # 匹配 "assetId":"XXXXX" 或 assetId: "XXXXX"
            match = re.search(r'assetId["\']?\s*[:=]\s*["\']([^"\']+)["\']', res.text)
            
            # 方案 2：搜索你找到的 cdi.ofiii.com 链接模式
            if not match:
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', res.text)
            
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 抓取成功: {aid}")
                return aid
            else:
                # 如果还是失败，把网页存下来分析（在 Actions 日志里能看到部分特征）
                print(f"⚠️ {cid} 匹配失败。关键词搜索未命中。")
        else:
            print(f"❌ {cid} 页面访问失败: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 异常: {str(e)}")
    return None

def sync():
    # 频道配置
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    if not os.path.exists("workers.js"): return
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 这里的正则要匹配 workers.js 里的格式，请确保 workers.js 里的 key 结构正确
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(2)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 同步完成！")
    else:
        print("😭 全量搜索依然未命中，可能需要检查 workers.js 的 key 格式。")

if __name__ == "__main__":
    sync()
