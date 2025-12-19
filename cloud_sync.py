import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_asset_id_advanced(cid, slug):
    print(f"🔍 正在抓取频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        }
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.set_page_load_timeout(40)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 模拟进入 JS：给网页加载和脚本执行的时间
        time.sleep(10)

        # 尝试通过 JS 强制点击或滚动，激活播放器逻辑
        try:
            driver.execute_script("window.scrollTo(0, 200);")
            # 尝试定位播放容器并模拟一个点击，触发 m3u8 请求
            container = driver.find_element(By.TAG_NAME, "body")
            container.click()
            print("🖱️ 已模拟点击页面，激活 JS 加载...")
        except:
            pass

        # 检查网络请求流
        for _ in range(5): # 循环检查 5 次
            for request in driver.requests:
                if 'master.m3u8' in request.url:
                    match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                    if match:
                        aid = match.group(1)
                        print(f"✅ 成功拦截 {cid} ID: {aid}")
                        return aid
            time.sleep(3)
            
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
    
    if not os.path.exists("workers.js"): return
    with open("workers.js", "r", encoding="utf-8") as f: content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]+?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
        time.sleep(2)

    if updated:
        with open("workers.js", "w", encoding="utf-8") as f: f.write(content)
        print("🚀 同步完成！")

if __name__ == "__main__":
    main()
