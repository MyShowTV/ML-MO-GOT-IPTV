import os, re, time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_static(cid, slug):
    print(f"🔍 正在抓取频道: {cid}...")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--proxy-server=http://127.0.0.1:7890')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(10) # 等待页面渲染

        html = driver.page_source
        # 核心逻辑：直接从网页的 Next.js 结构中找钥匙
        match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', html)
        if match:
            aid = match.group(1)
            print(f"✅ 【成功】 {cid} -> {aid}")
            return aid
        
        # 备选：从 m3u8 地址中找
        match = re.search(r'playlist/([a-zA-Z0-9_-]+)/master\.m3u8', html)
        if match:
            aid = match.group(1)
            return aid

        print(f"❌ {cid} 失败：源码中未找到钥匙")
    except Exception as e:
        print(f"🔥 {cid} 异常: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    # 频道对应表
    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv03': 'litv-longturn18',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02',
    }
    
    if not os.path.exists("workers.js"):
        print("❌ 找不到 workers.js")
        return
        
    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_static(cid, slug)
        if aid:
            # 精准匹配：寻找 "lhtv01": { ... key: "..." } 并替换
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(2)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 数据已成功写回 workers.js")
    else:
        print("😭 未捕获到任何新数据。")

if __name__ == "__main__":
    main()
