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
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        }
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        # 访问频道页
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 模拟点击触发播放器加载
        time.sleep(12)
        driver.execute_script("document.querySelector('body').click();")
        
        print(f"⏳ 正在监听数据流 (Target: {slug})...")
        time.sleep(15) # 给足时间让它加载你说的那个 .m3u8

        # 遍历所有请求，寻找包含你提到的特征串的 URL
        for request in reversed(driver.requests):
            url = request.url
            # 这里的正则匹配你发现的那种带 avc1/mp4a 的 master 或 index 路径
            if '.m3u8' in url and ('avc1' in url or 'playlist' in url):
                # 从路径中提取那串“钥匙” (AssetID)
                # 通常在 /playlist/ 之后，或者 /ocean/video/ 之后
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
    # 频道对应关系
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
            # 替换 workers.js 里的占位符
            pattern = rf'"{cid}"\s*:\s*\{{.*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated = True
        time.sleep(2)

    if updated:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 全部频道密匙已更新至 workers.js")

if __name__ == "__main__":
    main()
