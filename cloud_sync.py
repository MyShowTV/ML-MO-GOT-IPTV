import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_advanced(cid, slug):
    print(f"🔍 正在抓取频道: {cid} (Slug: {slug})...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890', # 对齐 Clash 端口
            'https': 'http://127.0.0.1:7890',
        },
        'connection_timeout': 60
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(15) # 增加等待时间确保 m3u8 加载

        for request in reversed(driver.requests):
            if 'master.m3u8' in request.url:
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"✅ 【拦截成功】 {cid} ID: {aid}")
                    return aid
    except Exception as e:
        print(f"🔥 {cid} 异常: {e}")
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
    
    if not os.path.exists("workers.js"): return
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            # 精准匹配 JSON 结构并替换 key
            pattern = rf'"{cid}"\s*:\s*\{{.*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                any_updated = True
        time.sleep(3)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 [SUCCESS] 同步完成")

if __name__ == "__main__":
    main()
