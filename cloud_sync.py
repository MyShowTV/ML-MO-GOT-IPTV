import os, re, time, requests

def get_asset_id(cid, slug):
    # 既然你能在 Network 看到请求，说明数据来自此接口
    # 这是 Ofiii 频道/视频信息的原始 JSON 数据接口
    api_url = f"https://www.ofiii.com/api/content/getSetAndVideoBySetId?setId={slug}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://www.ofiii.com/channel/watch/{slug}",
        "Accept": "application/json"
    }
    
    # 必须通过台湾代理，否则 API 会返回 403 或空数据
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # 直接在返回的 JSON 中精准搜索 assetId
            match = re.search(r'"assetId":"([a-zA-Z0-9_-]+)"', res.text)
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 接口抓取成功: {aid}")
                return aid
            else:
                print(f"⚠️ {cid} 接口返回数据中未包含 assetId")
        else:
            print(f"❌ {cid} 接口请求失败，状态码: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 网络异常: {str(e)}")
    return None

def sync():
    # 频道 slug 映射
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    if not os.path.exists("workers.js"):
        print("错误: 找不到 workers.js")
        return

    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 精确匹配 workers.js 里的 key 并更新
            # 支持格式如 "lhtv01": { key: "xxxx" }
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(1)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 同步成功！Cloudflare Workers 很快就会生效。")
    else:
        print("😭 未能更新任何频道，请检查 workers.js 格式。")

if __name__ == "__main__":
    sync()
