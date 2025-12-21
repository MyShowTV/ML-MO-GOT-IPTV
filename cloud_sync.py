import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_asset_id(cid, slug):
    print(f"🔍 正在深入探测频道: {cid} ({slug})")
    chromedriver_autoinstaller.install()
    
    proxy_user = "brd-customer-hl_739668d7-zone-datacenter_proxy1-country-tw"
    proxy_pass = "di168nnr7bb9"
    proxy_url = f'http://{proxy_user}:{proxy_pass}@brd.superproxy.io:33335'

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled') # 隐藏自动化特征
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    sw_options = {
        'proxy': {'http': proxy_url, 'https': proxy_url},
        'connection_timeout': 60,
        'verify_ssl': False 
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.set_page_load_timeout(60)
        
        # 访问页面
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # --- 关键修改 1：模拟人类等待 ---
        print("⏳ 正在模拟人类观看，等待数据包产生...")
        time.sleep(30) # 延长到 30 秒，让广告或初始加载完成
        
        # --- 关键修改 2：强制触发点击（唤醒播放器） ---
        try:
            # 尝试点击页面中心，绕过可能的“点击播放”遮罩
            driver.execute_script("document.elementFromPoint(window.innerWidth/2, window.innerHeight/2).click();")
            print("🖱️ 已执行模拟点击")
        except:
            pass
        
        time.sleep(10) # 点击后再等 10 秒

        # --- 关键修改 3：更宽泛的匹配规则 ---
        for request in reversed(driver.requests):
            url = request.url
            # 只要包含 playlist 且后缀是 .m3u8 的通常就是我们要的
            if '.m3u8' in url and 'playlist' in url:
                # 匹配 URL 中的 ID 部分
                match = re.search(r'playlist/([a-z0-9A-Z_-]+)/', url)
                if match:
                    aid = match.group(1)
                    print(f"✨ 抓取成功! {cid} -> {aid}")
                    return aid
                    
        print(f"❌ {cid} 还是没找到包，可能是数据中心IP被屏蔽，或者加载太慢")
    except Exception as e:
        print(f"🔥 运行异常: {e}")
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
    if not os.path.exists(worker_path): return
    with open(worker_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id(cid, slug)
        if aid:
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
            
    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 workers.js 更新完毕")

if __name__ == "__main__":
    main()
