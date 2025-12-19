import os, re, time, json
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_asset_id_advanced(cid, slug):
    print(f"🔍 抓取频道: {cid} ({slug})")
    chromedriver_autoinstaller.install()

    caps = webdriver.DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--mute-audio')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options, desired_capabilities=caps)
    driver.set_page_load_timeout(45)
    driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
    time.sleep(18)

    # 尝试主动播放视频
    try:
        driver.execute_script("""
        var v=document.querySelector('video');
        if(v){v.muted=true;v.play();}
        document.dispatchEvent(new MouseEvent("click", {bubbles:true,cancelable:true,view:window}));
        """)
    except:
        pass

    aid = None
    logs = driver.get_log('performance')
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
        except Exception:
            continue

    if not aid:
        print(f"❌ {cid}: 未发现 m3u8 请求")
    driver.quit()
    return aid

def main():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }

    if not os.path.exists("workers.js"):
        print("❌ 找不到 workers.js")
        return

    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^{{}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content, n = re.subn(pattern, replacement, content)
            if n > 0:
                updated = True
        time.sleep(4)

    if updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 成功同步到 workers.js")
    else:
        print("😢 没有任何更新。")

if __name__ == "__main__":
    main()
