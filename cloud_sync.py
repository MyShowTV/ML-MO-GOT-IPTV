import os, re, time, requests, json
import urllib3

# 禁用警告信息，让日志更干净
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    print(f"🔍 正在处理频道: {cid}...")
    
    # 你的 API 信息
    API_TOKEN = "76b7e42b-9c49-4acb-819a-3f90b45be668"
    ZONE_NAME = "unblocker_ofiii"
    
    api_url = "https://api.brightdata.com/request"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # --- 核心改进：增加渲染和等待 ---
    data = {
        "zone": ZONE_NAME,
        "url": f"https://www.ofiii.com/channel/watch/{slug}",
        "format": "raw",
        "country": "tw",
        "render": True,           # 必须开启！模拟浏览器渲染 JS
        "wait_for": ".video-player", # 等待播放器容器出现
        "timeout": 60000          # 延长等待时间
    }

    try:
        # 使用 POST 方式请求 API 接口
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=120, verify=False)
        
        if response.status_code == 200:
            content = response.text
            # 改进正则：Ofiii 的地址通常包含在脚本或特定的 URL 模式中
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            
            if not match:
                # 备用匹配模式
                match = re.search(r'assetId["\']:\s*["\']([^"\']+)["\']', content)

            if match:
                aid = match.group(1)
                print(f"✨ 抓取成功: {cid} -> {aid}")
                return aid
            else:
                # 如果没找到，打印一小段源码看看网页长什么样（方便调试）
                print(f"⚠️ 没发现 ID。网页标题: {re.search(r'<title>(.*?)</title>', content).group(1) if '<title>' in content else '未知'}")
        else:
            print(f"❌ API 报错: {response.status_code}")
            
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
    if not os.path.exists(worker_file): return

    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(5) # 频道之间多等一会儿

    if updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 workers.js 已更新！")

if __name__ == "__main__":
    main()
