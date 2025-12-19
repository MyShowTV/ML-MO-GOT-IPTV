import os, re, time, requests

def get_asset_id(cid, slug):
    # 这是 Ofiii 频道信息的真实数据接口，setId 就是 slug
    api_url = f"https://www.ofiii.com/api/content/getSetAndVideoBySetId?setId={slug}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://www.ofiii.com/channel/watch/{slug}",
        "Accept": "application/json"
    }
    # 必须走台湾代理
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            data = res.text
            # 直接在 JSON 返回结果中搜 assetId
            match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', data)
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 接口抓取成功: {aid}")
                return aid
            else:
                print(f"⚠️ {cid} 接口返回成功但未找到 assetId 字段")
        else:
            print(f"❌ {cid} API 错误，状态码: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 网络异常: {str(e)}")
    return None

def sync():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    file_path = "workers.js"
    if not os.path.exists(file_path): return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 这里的正则要确保能匹配到你 workers.js 的格式
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
            else:
                print(f"❓ {cid} 抓到了 ID 但 workers.js 里没找到对应的 key 行")

    if any_updated:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 API 同步成功！")
    else:
        print("😭 依然未能更新，请确认 workers.js 里的频道 ID 是否写对。")

if __name__ == "__main__":
    sync()
