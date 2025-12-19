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
    # 必须提供完整的、真实的 UA，防止被网站识别为爬虫
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # 允许自动播放
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
        
        # 1. 访问网页
        driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
        time.sleep(12) # 等待初始框架加载

       # 2. 执行 JS 强行点击所有 video 标签和播放器按钮
        print("🖱️ 正在执行 JS 交互逻辑...")
        js_script = """
            // 尝试播放页面上所有的 video 标签
            var videos = document.getElementsByTagName('video');
            for(var i=0; i<videos.length; i++) {
                videos[i].play();
            }
            // 模拟点击页面中心
            var evt = document.createEvent("MouseEvents");
            // 注意：下面这一行的 True 必须改为小写的 true
            evt.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
            document.dispatchEvent(evt);
        """
        driver.execute_script(js_script)
        
        # 3. 实时滚动页面，触发某些基于视口的懒加载 JS
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, {200 * (i+1)});")
            time.sleep(2)

        # 4. 关键：在 30 秒内持续扫描请求流
        print("📡 正在监听网络流量中的 m3u8 请求...")
        end_time = time.time() + 30
        while time.time() < end_time:
            # 倒序检查请求，通常最新的请求更可能是目标
            for request in reversed(driver.requests):
                if 'master.m3u8' in request.url:
                    # 匹配地址中的 ID 字符串
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
            # 清理请求记录，防止干扰下一个频道的抓取
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
            # 这里的正则要匹配 workers.js 中的具体格式
            pattern = rf'"{cid}"\s*:\s*\{{[^}}]*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                any_updated = True
        # 频道抓取间歇，防止被封 IP
        time.sleep(5)

    if any_updated:
        with open("workers.js", "w", encoding="utf-8") as f:
            f.write(content)
        print("🚀 [SUCCESS] 所有抓取到的 ID 已同步至 workers.js")
    else:
        print("😭 遗憾：未能捕获任何有效数据。")

if __name__ == "__main__":
    main()
