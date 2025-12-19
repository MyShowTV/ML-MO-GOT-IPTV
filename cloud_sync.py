import os, re, time, json
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_advanced(cid, slug):
    print(f"🔍 正在抓取频道: {cid} -> {slug}")
    chromedriver_autoinstaller.install()

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # 使用 DevTools 协议代替 selenium-wire
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
    time.sleep(15)

    logs = driver.get_log('performance')
    aid = None
    for entry in logs:
        try:
            msg = json.loads(entry['message'])
            url = msg['message']['params'].get('request', {}).get('url', '')
            if 'master.m3u8' in url:
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', url)
                if match:
                    aid = match.group(1)
                    print(f"✅ 捕获成功: {aid}")
                    break
        except:
            pass

    if not aid:
        print(f"❌ {cid}: 未找到 m3u8 请求")
    driver.quit()
    return aid

def main():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }

    if not os.path.exists("workers.js"):
        print("❌ 未找到 workers.js")
        return

    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^{{}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content, n = re.subn(pattern, replacement, content)
            if n > 0:
                any_updated = True
        time.sleep(5)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 更新成功！workers.js 已同步最新 key。")
    else:
        print("😭 未更新任何 key。")

if __name__ == "__main__":
    main()
