import os, re, time, requests, json
import urllib3

# 禁用安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    print(f"🌐 启动真机模拟 [频道: {cid}]...")
    
    # --- 必须确保这些信息与你截图中的“直接 API 访问”完全一致 ---
    API_TOKEN = "76b7e42b-9c49-4acb-819a-3f90b45be668"
    ZONE = "unblocker_ofiii" 
    
    url = "https://api.brightdata.com/request"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # 深度模拟真实 PC 浏览器行为
    payload = {
        "zone": ZONE,
        "url": f"https://www.ofiii.com/channel/watch/{slug}",
        "format": "raw",
        "country": "tw",
        "render": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "actions": [
            {"wait": ".video-player"},
            {"click": ".vjs-big-play-button"}, # 点击播放按钮
            {"wait": 8000}                     # 等待数据加载
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            content = response.text
            # 提取 AssetID
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            if match:
                aid = match.group(1)
                print(f"✅ 成功获取 ID: {aid}")
                return aid
            else:
                print("⚠️ 页面已渲染但未匹配到 ID。可能是选择器变化或区域限制。")
        elif response.status_code == 401:
            print("❌ 验证失败 (401): 请检查 Token 是否过期，或 Zone 名称是否正确。")
        else:
            print(f"❌ API 错误: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"🔥 网络异常: {e}")
    return None

def main():
    # 频道列表
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

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 更新 workers.js 里的 key
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(10) # 模拟真机需要时间间隔

    if updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 数据同步成功！")
    else:
        print("💡 无数据变动。")

if __name__ == "__main__":
    main()
