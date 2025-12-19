import os, re, time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_asset_id_static(cid, slug):
    print(f"🔍 正在抓取频道: {cid} (Slug: {slug})...")
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
        time.sleep(10) 

        html = driver.page_source
        # 从网页 JSON 结构中提取 assetId
        match = re.search(r'"assetId"\s*:\s*"([a-zA-Z0-9_-]+)"', html)
        if match:
            aid = match.group(1)
            print(f"✅ 【成功】 {cid} -> {aid}")
            return aid
        
        print(f"❌ {cid} 失败：源码中未找到钥匙")
    except Exception as e:
        print(f"🔥 {cid} 异常: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    # 完整的 7 个频道对应关系
    channels = {
        'lhtv01': 'litv-longturn03', # 龙华电影
        'lhtv02': 'litv-longturn21', # 龙华经典
        'lhtv03': 'litv-longturn18', # 龙华戏剧
        'lhtv04': 'litv-longturn11', # 龙华日韩
        'lhtv05': 'litv-longturn12', # 龙华偶像
        'lhtv06': 'litv-longturn01', # 龙华卡通
        'lhtv07': 'litv-longturn02', # 龙华洋片
    }
    
    if not os.path.exists("workers.js"):
        print("❌ 错误: 找不到 workers.js 文件")
        return
        
    with open("workers.js", "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_static(cid, slug)
        if aid:
            # 这里的正则匹配 workers.js 中的 key: "..." 结构
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        time.sleep(3) # 避免抓取过快

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 [SUCCESS] 所有频道钥匙已更新至 workers.js")
    else:
        print("😭 未能捕获到任何新数据。")

if __name__ == "__main__":
    main()
