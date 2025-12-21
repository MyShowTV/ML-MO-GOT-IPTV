import os, re, time, requests, json

def get_asset_id(cid, slug):
    print(f"🔍 正在通过 API 请求频道: {cid}...")
    
    # --- 这里的配置必须准确 ---
    # 这就是你发给我的那个长字符串
    API_TOKEN = "76b7e42b-9c49-4acb-819a-3f90b45be668" 
    ZONE_NAME = "unblocker_ofiii"
    
    # 这是 Bright Data 的高级请求接口，不是普通的代理端口
    api_url = "https://api.brightdata.com/request"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # 构造发送给云端的指令
    data = {
        "zone": ZONE_NAME,
        "url": f"https://www.ofiii.com/channel/watch/{slug}",
        "format": "raw",      # 获取网页原文
        "country": "tw",     # 强制指定台湾 IP
        "render": True       # 开启云端浏览器渲染（非常重要！）
    }

    try:
        # 注意：这里是 requests.post 而不是 get
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=120)
        
        if response.status_code == 200:
            content = response.text
            # 在返回的渲染后的 HTML 中搜索 AssetID
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            if match:
                aid = match.group(1)
                print(f"✅ 成功抓取: {cid} -> {aid}")
                return aid
            else:
                print(f"⚠️ 网页已打开，但没找到播放地址。")
        else:
            print(f"❌ API 报错: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"🔥 程序异常: {e}")
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    worker_file = "workers.js"
    if not os.path.exists(worker_file):
        print("❌ 找不到 workers.js")
        return

    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    is_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 修改这里的正则，确保匹配你的 workers.js 格式
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            is_updated = True
        time.sleep(5) # 稍微慢一点，保证成功率

    if is_updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🎉 全部频道已更新完毕！")

if __name__ == "__main__":
    main()
