import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id(cid, slug):
    print(f"🔍 启动浏览器抓取: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 这里的代理必须指向本地 Clash 开启的 7890 端口
    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        },
        'connection_timeout': 60
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.set_page_load_timeout(45)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 动态加载等待
        time.sleep(15)
        
        for request in driver.requests:
            if 'master.m3u8' in request.url:
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"✅ 抓取成功: {aid}")
                    return aid
        print(f"⚠️ {cid} 未拦截到 master.m3u8")
    except Exception as e:
        print(f"🔥 {cid} 错误: {e}")
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
    
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]+?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
        time.sleep(5)

    if updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 同步数据成功")

if __name__ == "__main__":
    main()
