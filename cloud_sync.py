import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_asset_id_advanced(cid, slug):
    print(f"🔍 正在深度抓取频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--autoplay-policy=no-user-gesture-required')

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
        time.sleep(12)

        js_script = """
            var videos = document.getElementsByTagName('video');
            for(var i=0; i<videos.length; i++) {
                videos[i].play();
            }
            var evt = document.createEvent("MouseEvents");
            evt.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
            document.dispatchEvent(evt);
        """
        driver.execute_script(js_script)
        
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, {200 * (i+1)});")
            time.sleep(2)

        print("📡 正在监听网络流量中的 m3u8 请求...")
        end_time = time.time() + 30
        while time.time() < end_time:
            for request in reversed(driver.requests):
                if 'master.m3u8' in request.url:
                    match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                    if match:
                        aid = match.group(1)
                        print(f"✅ 【拦截成功】 {cid} ID: {aid}")
                        return aid
            time.sleep(4)
            
        print(f"❌ {cid} 截获超时：未发现 master.m3u8 请求。")
    except Exception as e:
        print(f"🔥 {cid} 运行时异常: {e}")
    finally:
        if driver:
            del driver.requests
            driver.quit()
    return None

def main():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    if not os.path.exists("workers.js"):
        print("❌ 错误: 找不到 workers.js")
        return
        
    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(5)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 [SUCCESS] 所有抓取到的 ID 已同步至 workers.js")
    else:
        print("😭 未能捕获任何有效数据。")

if __name__ == "__main__":
    main()
