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
    配置并启动浏览器，确保驱动下载跳过代理，而抓取过程使用代理。
    """
    # --- 1. 临时禁用环境变量代理，以确保驱动下载成功 ---
    env_copy = os.environ.copy()
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    
    try:
        logger.info("🚚 正在检查并下载 ChromeDriver (跳过代理)...")
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
    finally:
        # 还原环境变量
        os.environ.update(env_copy)

    # --- 2. 配置浏览器选项 ---
    options = Options()
    options.add_argument('--headless=new')  # 使用最新的无头模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    # 模拟真实浏览器 User-Agent
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    # 强制浏览器走 SOCKS5 代理
    # 注意：10808 是你在 main.yml 中 ss-local 映射的本地端口
    options.add_argument('--proxy-server=socks5://127.0.0.1:10808')

    return webdriver.Chrome(service=service, options=options)

def update_workers_js(results):
    """
    将抓取到的 AssetID 更新回 workers.js 文件
    """
    file_path = "workers.js"
    if not os.path.exists(file_path):
        logger.error(f"❌ 未找到 {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated_count = 0
    for cid, aid in results.items():
        # 匹配模式： "lhtv01": { ... key: "旧ID" }
        # \1 代表匹配到的前缀部分，后面替换为新的 aid
        pattern = rf'("{cid}":\s*\{{[^{{}}]+key:\s*")[^"]*"'
        if re.search(pattern, content):
            content = re.sub(pattern, rf'\1{aid}"', content)
            updated_count += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"🎉 成功更新了 {updated_count} 个频道的 AssetID")

def main():
    # 需要抓取的频道列表
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
        # --- 诊断：确认 IP 是否为台湾 VPS ---
        try:
            driver.get("http://ifconfig.me/ip")
            time.sleep(2)
            ip = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"🌍 浏览器当前出口 IP: {ip}")
        except:
            logger.warning("⚠️ 无法确认 IP，将尝试直接抓取。")

        # --- 循环抓取 ---
        for cid, slug in channels.items():
            logger.info(f"🔍 正在抓取频道: {cid} ({slug})")
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            
            driver.get(url)
            time.sleep(15)  # 给予充足的渲染时间

            # 策略 1: 从 window.__PRELOADED_STATE__ 读取 (最精准)
            found_id = driver.execute_script("""
                try {
                    return window.__PRELOADED_STATE__.video.programInfo.assetId;
                } catch(e) {
                    return null;
                }
            """)

            # 策略 2: 如果策略 1 失败，通过正则寻找 URL 中的特征 (PKIOGb6cWYI 格式)
            if not found_id:
                html = driver.page_source
                # 寻找 playlist 路径中的 11 位特征 ID
                match = re.search(r'/video/playlist/([a-zA-Z0-9_-]{10,12})/', html)
                if match:
                    found_id = match.group(1)
                else:
                    # 备选正则：通用 assetId 匹配
                    match_alt = re.search(r'["\']assetId["\']\s*:\s*["\']([^"\']+)["\']', html)
                    if match_alt:
                        found_id = match_alt.group(1)

            if found_id:
                logger.info(f"✅ 抓取成功 {cid}: {found_id}")
                results[cid] = found_id
            else:
                logger.warning(f"❌ 抓取失败 {cid}，当前页面标题: {driver.title}")

        # --- 保存结果 ---
        if results:
            update_workers_js(results)
        else:
            logger.error("🚫 所有频道均未抓取到 ID，请检查代理是否稳定。")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
