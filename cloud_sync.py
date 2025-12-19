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
            # 方案 1：搜索现代网页常用的 JSON 数据块 (Next.js 常用格式)
            # 搜索 __NEXT_DATA__ 标签中的内容
            next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if next_data:
                try:
                    data_json = json.loads(next_data.group(1))
                    # 在复杂的 JSON 树中模糊搜索 assetId
                    json_str = json.dumps(data_json)
                    asset_match = re.search(r'"assetId":"([a-zA-Z0-9_-]+)"', json_str)
                    if asset_match:
                        aid = asset_match.group(1)
                        print(f"✅ {cid} 成功 (JSON): {aid}")
                        return aid
                except:
                    pass

            # 方案 2：如果 JSON 块失效，尝试万能模糊匹配（匹配 master.m3u8 前面那串 ID）
            # 匹配类似："/path/to/ABC_123_XYZ/master.m3u8" 中的 ABC_123_XYZ
            fuzzy_match = re.search(r'\/([a-zA-Z0-9_-]+)\/master\.m3u8', res.text)
            if fuzzy_match:
                aid = fuzzy_match.group(1)
                print(f"✅ {cid} 成功 (模糊): {aid}")
                return aid
                
            print(f"⚠️ {cid} 抓取失败：网页已打开但 ID 隐藏太深")
        else:
            print(f"❌ {cid} 状态码: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 网络异常: {str(e)}")
    return None

def sync():
    # 根据你之前的测试，修正后的最新路径
    channels = {
        'lhtv01': 'channel/watch/litv-longturn03',
        'lhtv03': 'channel/watch/litv-longturn02',
        'lhtv05': 'channel/watch/ofiii73', # 200 的先跑通
        'lhtv06': 'channel/watch/ofiii74',
        'lhtv07': 'channel/watch/ofiii76',
    }
    
    if not os.path.exists("workers.js"): return
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    any_updated = False
    for cid, path in channels.items():
        aid = get_asset_id(cid, path)
        if aid:
            # 适配 workers.js 的替换逻辑
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(2) # 增加延迟，防止被反爬

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 同步完成，请检查 Cloudflare Workers！")

if __name__ == "__main__":
    sync()
