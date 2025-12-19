import os, re, time, requests

def get_asset_id(cid, path):
    url = f"https://www.ofiii.com/{path}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.ofiii.com/"
    }
    proxies = {
        "http": os.environ.get("HTTP_PROXY"),
        "https": os.environ.get("HTTPS_PROXY")
    }
    
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=20)
        # 如果 404，尝试去掉 'watch/' 路径再试一次
        if res.status_code == 404 and 'watch/' in path:
            new_path = path.replace('watch/', '')
            return get_asset_id(cid, new_path)
            
        # 增强版正则：不仅找 m3u8，还直接找 json 中的 assetId
        patterns = [
            r"playlist/([a-zA-Z0-9_-]{8,})/master\.m3u8",
            r'"assetId"\s*:\s*"([^"]+)"',
            r'asset_id\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for p in patterns:
            match = re.search(p, res.text)
            if match:
                aid = match.group(1)
                print(f"✅ {cid} 抓取成功: {aid}")
                return aid
        
        print(f"⚠️ {cid} 无法从页面提取钥匙，状态码: {res.status_code}")
        return None
    except Exception as e:
        print(f"🔥 {cid} 请求异常: {str(e)}")
        return None

def sync():
    # 更新了最新的官方路径
    channels = {
    'lhtv01': 'channel/watch/litv-longturn03',
    'lhtv02': 'channel/watch/litv-longturn05',
    'lhtv03': 'channel/watch/litv-longturn02',
    'lhtv04': 'channel/watch/litv-longturn04',
    'lhtv05': 'channel/watch/litv-longturn01',
    'lhtv06': 'channel/watch/litv-longturn06',
    'lhtv07': 'channel/watch/litv-longturn07',
}
    
    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    success_count = 0
    for cid, path in channels.items():
        aid = get_asset_id(cid, path)
        if aid:
            # 修改了匹配模式，使其更兼容你的 workers.js 结构
            pattern = rf'("{cid}":\s*\{{[^}}]*key:\s*")([^"]*)(")'
            content = re.sub(pattern, rf'\1{aid}\3', content)
            success_count += 1
        time.sleep(2)

    if success_count > 0:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"🎉 成功同步 {success_count} 个频道")
    else:
        print("😭 依然抓取不到，请更换 clash_config.yaml 里的节点")
        exit(1)

if __name__ == "__main__":
    sync()
