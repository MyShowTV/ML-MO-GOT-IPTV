import os, re, time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_asset_id_advanced(cid, slug):
    print(f"🚀 开始深度抓取频道: {cid}")
    chromedriver_autoinstaller.install()
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # 模拟真实浏览器特征
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--autoplay-policy=no-user-gesture-required') # 尝试允许自动播放

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
        driver.set_page_load_timeout(30)
        
        # 1. 打开网页
        url = f"https://www.ofiii.com/channel/watch/{slug}"
        driver.get(url)
        print("🌐 网页已打开，等待加载...")

        # 2. 模拟进入 JS：滚动页面触发懒加载
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)

        # 3. 查找并点击播放按钮 (如果存在)
        # Ofiii 有时会有一个大的中央播放按钮，或者是在加载失败时出现重试按钮
        try:
            # 这里的 Selector 根据 Ofiii 实际 DOM 结构调整，通常是 .play-button 或包含 play 文本的元素
            # 我们使用更通用的逻辑：寻找屏幕中心可能存在的按钮并点击
            wait = WebDriverWait(driver, 10)
            play_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'play')] | //div[contains(@class, 'play')]")))
            play_btn.click()
            print("🖱️ 已点击播放按钮，触发 JS 加载流媒体...")
        except Exception:
            print("ℹ️ 未发现显式播放按钮，可能已自动开始加载。")

        # 4. 关键：循环监控网络请求，等待 master.m3u8 出现
        # 模拟停留较长时间，确保 JS 完成混淆解密并发出请求
        start_time = time.time()
        while time.time() - start_time < 30: # 最多等 30 秒
            for request in driver.requests:
                if 'master.m3u8' in request.url:
                    match = re.search(r'playlist/([a-zA-Z0-9_-]+)/', request.url)
                    if match:
                        aid = match.group(1)
                        print(f"🎯 成功拦截流地址! ID: {aid}")
                        return aid
            time.sleep(3) # 每 3 秒检查一次请求列表

    except Exception as e:
        print(f"🔥 运行出错: {e}")
    finally:
        if driver: driver.quit()
    return None

# ... main 函数保持不变，调用 get_asset_id_advanced 即可 ...
