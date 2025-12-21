import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_advanced(cid, slug):
    print(f"🔍 正在深入探测频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # 住宅代理省流配置：禁用图片加载
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

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
        driver.set_page_load_timeout(40)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 模拟交互触发加载
        time.sleep(15)
        driver.execute_script("document.querySelector('body').click();")
        
        print(f"⏳ 正在监听数据流...")
        time.sleep(10) 

        # 遍历请求寻找 AssetID
        for request in reversed(driver.requests):
            url = request.url
            if '.m3u8' in url and ('playlist' in url or 'master' in url):
                match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', url)
                if match:
                    aid = match.group(1)
                    print(f"✨ 【发现密匙】 {cid} -> {aid}")
                    return aid
                    
        print(f"❌ {cid} 抓取失败：未捕获到关键数据包")
    except Exception as e:
        print(f"🔥 {cid} 错误: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    worker_path = "workers.js"
    if not os.path.exists(worker_path):
        print("❌ 错误: 找不到 workers.js")
        return

    with open(worker_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            # 精确匹配 workers.js 里的 key 结构并替换
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(3)

    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 密匙已成功同步至 workers.js")

if __name__ == "__main__":
    main()
