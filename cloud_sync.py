import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_advanced(cid, slug):
    print(f"🔍 探测频道: {cid} ({slug})")
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    proxy_url = os.getenv("BD_PROXY")
    sw_options = {'proxy': {'http': proxy_url, 'https': proxy_url}} if proxy_url else {}

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(10)
        driver.execute_script("document.querySelector('body').click();")
        print(f"⏳ 正在监听数据流: {slug}")
        time.sleep(15)

        for request in reversed(driver.requests):
            url = request.url
            if '.m3u8' in url and ('avc1' in url or 'playlist' in url):
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', url)
                if match:
                    aid = match.group(1)
                    print(f"✨ 发现密钥 {cid} → {aid}")
                    return aid
        print(f"❌ {cid} 未发现关键请求")
    except Exception as e:
        print(f"🔥 {cid} 错误: {e}")
    finally:
        if driver:
            driver.quit()
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }

    worker_path = "workers.js"
    with open(worker_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{.*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(2)

    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 全部频道密钥已更新到 workers.js")

if __name__ == "__main__":
    main()
