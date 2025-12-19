import os
import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_driver():
    """
    配置浏览器：
    1. 绕过自动化检测 (Anti-Bot)
    2. 设置 SOCKS5 代理
    3. 隔离驱动下载环境
    """
    # --- 1. 下载驱动 (跳过环境变量代理) ---
    env_copy = os.environ.copy()
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
        if var in os.environ:
            del os.environ[var]
    
    try:
        logger.info("🚚 正在准备 ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
    finally:
        os.environ.update(env_copy)

    # --- 2. 浏览器高级配置 ---
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    
    # 模拟真实浏览器特征
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置 SOCKS5 代理
    options.add_argument('--proxy-server=socks5://127.0.0.1:10808')

    driver = webdriver.Chrome(service=service, options=options)

    # --- 3. 关键：注入 JS 抹除 Selenium 痕迹 ---
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def update_workers_js(results):
    """更新 AssetID 到本地 workers.js"""
    file_path = "workers.js"
    if not os.path.exists(file_path):
        logger.error("❌ 找不到 workers.js")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated_count = 0
    for cid, aid in results.items():
        # 匹配频道对应的 key 字段进行替换
        pattern = rf'("{cid}":\s*\{{[^{{}}]+key:\s*")[^"]*"'
        if re.search(pattern, content):
            content = re.sub(pattern, rf'\1{aid}"', content)
            updated_count += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"🎉 已成功同步 {updated_count} 个频道的最新 ID 到文件")

def main():
    # 目标频道及其 Slug
    channels = {
        'lhtv01': 'litv-longturn01',
        'lhtv02': 'litv-longturn02',
        'lhtv03': 'litv-longturn03',
        'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn18',
        'lhtv07': 'litv-longturn21'
    }
    
    driver = get_driver()
    results = {}
    
    try:
        # 验证代理出口
        driver.get("http://ifconfig.me/ip")
        time.sleep(3)
        ip = driver.find_element(By.TAG_NAME, "body").text
        logger.info(f"🌍 代理工作正常，当前出口 IP: {ip}")

        for cid, slug in channels.items():
            logger.info(f"🔍 正在检索频道: {cid}")
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            
            driver.get(url)
            # 增加等待时间，确保 JS 渲染完成
            time.sleep(20) 

            # --- 多重提取策略 ---
            # 策略 A: 直接内存变量提取
            found_id = driver.execute_script("return window.__PRELOADED_STATE__?.video?.programInfo?.assetId;")

            # 策略 B: 搜索全页面源码中的 11 位特征字符 (对应你之前的 cdi URL)
            if not found_id:
                html = driver.page_source
                # 寻找包含在播放列表路径中的 11 位字符
                match_url = re.search(r'video/playlist/([a-zA-Z0-9_-]{11})/', html)
                if match_url:
                    found_id = match_url.group(1)
                else:
                    # 策略 C: 寻找 JSON 结构的 assetId
                    match_json = re.search(r'["\']assetId["\']\s*[:=]\s*["\']([^"\']{11})["\']', html)
                    if match_json:
                        found_id = match_json.group(1)

            if found_id:
                logger.info(f"✅ 获取成功 {cid} -> {found_id}")
                results[cid] = found_id
            else:
                logger.warning(f"⚠️ 无法在页面 {slug} 中提取 ID，可能是加载太慢或结构变动")

        if results:
            update_workers_js(results)
        else:
            logger.error("🚫 抓取任务结束，未获得任何有效 ID")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
