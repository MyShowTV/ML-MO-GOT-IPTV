import os, re, time, json
import chromedriver_autoinstaller
from seleniumwire import webdriver # 使用 selenium-wire 拦截请求
from selenium.webdriver.chrome.options import Options

def get_asset_id_by_selenium(cid, slug):
    """通过模拟浏览器拦截网络请求获取 ID"""
    print(f"🌐 正在模拟浏览器访问频道: {cid} ({slug})...")
    
    # 自动安装匹配版本的 ChromeDriver
    chromedriver_autoinstaller.install()
    
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 无头模式，必须开启
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # 走台湾 VPS 代理
    seleniumwire_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
            'no_proxy': 'localhost,127.0.0.1'
        },
        'detach': True # 拦截后立即释放
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
        driver.set_page_load_timeout(30)
        
        # 打开频道页面
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 给网页足够的执行 JS 的时间 (10-15秒)
        time.sleep(12)
        
        # 核心：遍历浏览器产生的所有网络请求
        for request in driver.requests:
            if request.response:
                # 寻找包含 master.m3u8 的请求地址
                if 'master.m3u8' in request.url:
                    # 从链接中正则提取 ID (例如 playlist/B8KQyHS-600/master.m3u8)
                    match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                    if match:
                        aid = match.group(1)
                        print(f"🎯 浏览器拦截成功! {cid} ID: {aid}")
                        return aid
        
        print(f"⚠️ {cid} 未能在请求流中拦截到 m3u8 地址")
    except Exception as e:
        print(f"🔥 Selenium 运行异常: {e}")
    finally:
        if driver:
            driver.quit()
    return None

def sync():
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn02',
        'lhtv05': 'ofiii73',
        'lhtv06': 'ofiii74',
        'lhtv07': 'ofiii76',
    }
    
    file_path = "workers.js"
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f: content = f.read()

    updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_by_selenium(cid, slug)
        if aid:
            # 替换 workers.js 里的 key
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]+?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                updated = True
        time.sleep(2)

    if updated:
        with open(file_path, "w", encoding="utf-8") as f: f.write(content)
        print("🚀 [SUCCESS] 模拟浏览器抓取并同步成功！")

if __name__ == "__main__":
    sync()
