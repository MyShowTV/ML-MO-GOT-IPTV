import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_asset_id_advanced(cid, slug):
    print(f"🔍 正在抓取频道: {cid} (Slug: {slug})...")
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
        },
        'connection_timeout': 60
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        
        # 等待页面加载并模拟交互触发播放器
        time.sleep(10)
        try:
            driver.execute_script("document.querySelector('body').click();")
            print(f"🖱️ 已发送模拟点击触发加载...")
        except:
            pass
        
        time.sleep(10) # 给 10 秒缓冲时间让 m3u8 刷出来

        # 逆序搜索请求记录，找到最新的 master.m3u8
        for request in reversed(driver.requests):
            if 'master.m3u8' in request.url:
                # 兼容多种路径模式提取 AssetId
                match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                if match:
                    aid = match.group(1)
                    print(f"✅ 【拦截成功】 {cid} -> ID: {aid}")
                    return aid
        print(f"❌ {cid} 失败：未发现有效数据包")
    except Exception as e:
        print(f"🔥 {cid} 报错: {e}")
    finally:
        if driver: driver.quit()
    return None

def main():
    # 频道配置列表
    channels = {
        'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18', 'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12', 'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }
    
    worker_file = "workers.js"
    if not os.path.exists(worker_file):
        print(f"🚫 找不到 {worker_file}")
        return
        
    with open(worker_file, "r", encoding="utf-8") as f:
        content = f.read()

    any_updated = False
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            # 这里的正则完美匹配 workers.js 里的 JSON 结构
            pattern = rf'"{cid}"\s*:\s*\{{.*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                any_updated = True
        time.sleep(2) # 频道间稍微停顿

    if any_updated:
        with open(worker_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 [SUCCESS] 脚本已更新 workers.js 文件内容")

if __name__ == "__main__":
    main()
