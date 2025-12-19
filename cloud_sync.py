import os, re, time, requests

def get_asset_id(path):
    url = f"https://www.ofiii.com/{path}"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.ofiii.com/"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        match = re.search(r"playlist/([a-zA-Z0-9_-]{8,})/master\.m3u8", res.text)
        return match.group(1) if match else None
    except:
        return None

def sync():
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

    for cid, path in channels.items():
        aid = get_asset_id(path)
        if aid:
            # 精准替换 workers.js 中对应 ID 的 key 值
            pattern = rf'("{cid}":\s*\{{[^}}]*key:\s*")([^"]*)(")'
            content = re.sub(pattern, rf'\1{aid}\3', content)
            print(f"✅ {cid} 更新为: {aid}")
        time.sleep(1)

    with open("workers.js", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    sync()
