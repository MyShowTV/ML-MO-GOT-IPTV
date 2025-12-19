import os, re, time, requests

def get_asset_id(cid, slug):
    # 直接请求数据接口，这通常是动态网页获取 ID 的源头
    api_url = f"https://www.ofiii.com/api/content/getSetAndVideoBySetId?setId={slug}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://www.ofiii.com/channel/watch/{slug}",
        "Accept": "application/json"
    }
    # 必须通过台湾代理
    proxies = { "http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890" }
    
    try:
        res = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
        if res.status_code == 200:
            # 在返回的 JSON 中提取 assetId
            match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', res.text)
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 抓取成功: {aid}")
                return aid
    except:
        pass
    
    # 备用方案：如果 API 失败，尝试抓取网页源码中的 Next.js 数据块
    try:
        page_url = f"https://www.ofiii.com/channel/watch/{slug}"
        res = requests.get(page_url, headers=headers, proxies=proxies, timeout=15)
        match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', res.text)
        if match:
            aid = match.group(1)
            print(f"✅ {cid} 网页抓取成功: {aid}")
            return aid
    except:
        pass
    
    print(f"❌ {cid} 所有抓取手段均失效")
    return None

def sync():
    # 这里的 ID 必须对应 workers.js 里的左侧名称
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
            # 精准替换：匹配 "cid": { ... key: "..." }
            # 无论你中间有多少空格或换行，都能精准捕捉
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]+?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
            else:
                print(f"⚠️ {cid} 抓到了 ID 但在 workers.js 中匹配不到格式")

    if any_updated:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 同步完成！Workers 代码已更新。")

if __name__ == "__main__":
    sync()
