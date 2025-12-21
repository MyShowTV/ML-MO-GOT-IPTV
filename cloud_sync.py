import os, re, time, requests, json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_asset_id(cid, slug):
    print(f"🔍 正在调用 Web Unlocker + 住宅 IP 模拟点击: {cid}...")
    
    # 1. 使用 API 模式，这是唯一支持 actions (点击) 的模式
    api_url = "https://api.brightdata.com/request"
    # 使用你之前成功的 API Token
    api_token = "76b7e42b-9c49-4acb-819a-3f90b45be668"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 构造指令：锁定台湾 + 强制住宅代理 + 执行点击
    data = {
        "zone": "unblocker_ofiii",     # 必须是 Web Unlocker 类型的 Zone
        "url": f"https://www.ofiii.com/channel/watch/{slug}",
        "format": "raw",
        "country": "tw",
        "proxy_type": "residential",   # 【关键】在这里指定走住宅流量
        "render": True,
        "actions": [
            {"wait": ".vjs-big-play-button"}, 
            {"click": ".vjs-big-play-button"}, 
            {"wait": 8000}              # 住宅 IP 较慢，给足 8 秒加载时间
        ]
    }

    try:
        # 注意这里是 POST 请求，直接发给 Bright Data 控制中心
        response = requests.post(api_url, headers=headers, json=data, timeout=120)
        
        if response.status_code == 200:
            content = response.text
            # 搜索 playlist/ID/
            match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', content)
            if match:
                aid = match.group(1)
                print(f"✨ 成功！住宅 IP 抓取到 ID: {aid}")
                return aid
            else:
                # 如果没找到 ID，打印前 200 字源码，看是否返回了错误页
                print(f"⚠️ 网页已返回，但未发现链接。预览: {content[:100].strip()}")
        else:
            print(f"❌ API 报错: {response.status_code} - {response.text[:100]}")
            
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
        time.sleep(10) # 住宅 API 任务重，增加间隔

    if updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 同步任务圆满完成！")

if __name__ == "__main__":
    main()
