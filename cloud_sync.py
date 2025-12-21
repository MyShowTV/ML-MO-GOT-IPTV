import os, re, time, requests, json
import urllib3

# 禁用证书警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    print(f"🔍 正在处理频道: {cid}...")
    
    # --- 核心配置：必须准确 ---
    # 这是你提供的 API Token
    API_TOKEN = "76b7e42b-9c49-4acb-819a-3f90b45be668"
    ZONE_NAME = "unblocker_ofiii"
    
    api_url = "https://api.brightdata.com/request"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # 指令包：强制渲染并等待视频播放器
    data = {
        "zone": ZONE_NAME,
        "url": f"https://www.ofiii.com/channel/watch/{slug}",
        "format": "raw",
        "country": "tw",
        "render": True,           # 开启云浏览器渲染
        "wait_for": "video",      # 关键：等视频组件加载出来
        "timeout": 40000          # 40秒超时
    }

    try:
        # 向 Bright Data 发送 POST 请求
        response = requests.post(api_url, headers=headers, json=data, timeout=120, verify=False)
        
        if response.status_code == 200:
            content = response.text
            # 正则搜索 playlist/ID/
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            if match:
                aid = match.group(1)
                print(f"✅ 成功提取: {aid}")
                return aid
            else:
                print("⚠️ 网页已打开，但没发现 ID。可能需要检查 Ofiii 是否改版。")
        else:
            print(f"❌ API 报错: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"🔥 异常: {e}")
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
        print("❌ 错误: 找不到 workers.js")
        return

    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 自动替换 workers.js 里的 key: "..."
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(5) 

    if updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 workers.js 更新完毕！")

if __name__ == "__main__":
    main()
