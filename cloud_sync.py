import os, re, time, requests

def get_asset_id(cid, channel_slug):
    # 直接请求 Ofiii 的内容信息接口，channel_slug 如 'litv-longturn03'
    api_url = f"https://www.ofiii.com/api/content/getSetAndVideoBySetId?setId={channel_slug}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://www.ofiii.com/channel/watch/{channel_slug}",
        "Accept": "application/json"
    }
    
    # 必须通过你的台湾 VPS 代理访问
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        # 直接拿接口数据
        res = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            data = res.json()
            # 这里的数据结构通常在 data['data']['videoList'][0]['assetId']
            # 我们用模糊搜索确保万无一失
            data_str = res.text
            match = re.search(r'"assetId":"([a-zA-Z0-9_-]+)"', data_str)
            
            if match:
                aid = match.group(1)
                print(f"✅ {cid} API 抓取成功: {aid}")
                return aid
            else:
                print(f"⚠️ {cid} 接口返回成功但未找到 assetId")
        else:
            print(f"❌ {cid} API 错误: {res.status_code}")
    except Exception as e:
        print(f"🔥 {cid} 网络异常: {str(e)}")
    return None

def sync():
    # 注意：这里的 ID 只需要最后的斜杠部分
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
            # 兼容 workers.js 的替换
            pattern = rf'"{cid}":\s*\{{[^}}]*?key:\s*"[^"]*"'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(1)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 API 同步模式完成！")

if __name__ == "__main__":
    sync()
