import os, re, time, requests, json

def get_asset_id(cid, path):
    url = f"https://www.ofiii.com/{path}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ofiii.com/",
        "Accept-Language": "zh-TW,zh;q=0.9"
    }
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # 方案 1：根据你 F12 发现的规律，匹配 /playlist/ 和 / 之间的任意字符
            # 这种方法最暴力但也最有效
            match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', res.text)
            
            # 方案 2：如果方案 1 没搜到，尝试在 JSON 数据块中搜索 assetId
            if not match:
                match = re.search(r'"assetId":"([a-zA-Z0-9_-]+)"', res.text)
            
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 抓取成功: {aid}")
                return aid
            else:
                # 最后的防线：如果还是找不到，打印前 500 个字符看看网页到底长啥样（方便调试）
                print(f"⚠️ {cid} 匹配失败，网页内容预览: {res.text[:200]}")
        else:
            print(f"❌ {cid} 状态码异常: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 网络异常: {str(e)}")
    return None

def sync():
    # 使用你确认过的路径
    channels = {
        'lhtv01': 'channel/watch/litv-longturn03',
        'lhtv03': 'channel/watch/litv-longturn02',
        'lhtv05': 'channel/watch/ofiii73',
        'lhtv06': 'channel/watch/ofiii74',
        'lhtv07': 'channel/watch/ofiii76',
    }
    
    if not os.path.exists("workers.js"): return
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    any_updated = False
    for cid, path in channels.items():
        aid = get_asset_id(cid, path)
        if aid:
            # 修改 workers.js 中的 key
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(2)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 同步完成！关键 Key 已更新。")

if __name__ == "__main__":
    sync()
