import os
import re
import time
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
M3U_PATH = os.path.join(BASE_DIR, "TWTV.m3u")

def log(message):
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{timestamp}] {message}")

def get_headless_driver():
    """配置适合云端运行的无头浏览器"""
    chromedriver_autoinstaller.install()
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 禁用图片加载以节省云端带宽
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    
    return webdriver.Chrome(options=chrome_options)

def crawl_chengdu(driver, name, slug):
    """成都频道抓取逻辑（无需代理）"""
    log(f"🔍 正在抓取: {name}")
    try:
        url = f"https://www.ofiii.com/channel/watch/{slug}"
        driver.get(url)
        
        # 等待播放按钮并点击（模拟你原本 iptv_main.py 中的逻辑）
        try:
            play_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button"))
            )
            play_btn.click()
            log(f"🖱️ {name}: 已点击播放按钮")
        except:
            log(f"ℹ️ {name}: 未发现播放按钮，尝试直接截获数据包")

        # 等待流数据加载
        time.sleep(20) 
        
        for request in reversed(driver.requests):
            if request.response:
                req_url = request.url
                # 根据你之前成功的日志，成都频道通常返回的是普通 m3u8 流
                if '.m3u8' in req_url and 'longturn' not in req_url:
                    log(f"✅ {name} 成功获取链接: {req_url[:60]}...")
                    return req_url
        log(f"⚠️ {name}: 未捕获到 m3u8 链接")
    except Exception as e:
        log(f"🔥 {name} 出错: {str(e)}")
    return None

def main():
    # 成都频道列表
    chengdu_channels = [
        {"name": "成都新闻综合", "slug": "cdtv-news"},
        {"name": "成都经济资讯", "slug": "cdtv-econ"},
        {"name": "成都都市生活", "slug": "cdtv-life"},
        {"name": "成都影视文艺", "slug": "cdtv-drama"},
        {"name": "成都公共", "slug": "cdtv-pub"},
        {"name": "成都少儿", "slug": "cdtv-kids"}
    ]

    driver = get_headless_driver()
    results = {}
    try:
        for ch in chengdu_channels:
            url = crawl_chengdu(driver, ch['name'], ch['slug'])
            if url:
                results[ch['name']] = url
            time.sleep(3) # 频道间隔
    finally:
        driver.quit()

    if results:
        log(f"🎉 任务结束，共捕获 {len(results)} 个成都频道地址")
        # 这里可以添加你之前的 m3u 替换逻辑

if __name__ == "__main__":
    main()
