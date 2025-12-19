import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id(cid, slug):
    print(f"🔍 正在抓取频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # 代理配置：必须通过你的台湾 VPS
    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        },
        'connection_timeout': 30
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.set_page_load_timeout(40)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 动态网页需要时间执行 JS，建议等待 15 秒
        time.sleep(15)
        
        for request in driver.requests:
            if 'master.m3u8' in request.url:
                # 从地址如 .../playlist/B8KQyHS-600/master.m3u8 提取 ID
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"✅ {cid} 抓取成功: {aid}")
                    return aid
        print(f"⚠️ {cid} 未拦截到 m3u8 请求")
    except Exception as e:
        print(f"🔥 {cid} 发生错误: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    file_path = "workers.js"
    if not os.path.exists(file_path):
        print("❌ 找不到 workers.js")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            # 兼容 workers.js 结构的正则替换
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]+?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(3)

    if any_updated:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 本地文件更新成功")
    else:
        print("😭 无数据更新")

if __name__ == "__main__":
    main()
