import os
import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 核心：防止 Selenium 内部通信走代理
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

    # 临时关闭代理以下载驱动
    old_proxy = os.environ.get('HTTPS_PROXY')
    os.environ['HTTPS_PROXY'] = ''
    service = Service(ChromeDriverManager().install())
    os.environ['HTTPS_PROXY'] = old_proxy if old_proxy else ''

    # 设置浏览器代理
    if old_proxy:
        proxy_server = old_proxy.replace("http://", "").replace("https://", "")
        options.add_argument(f'--proxy-server=http://{proxy_server}')
        # 排除本地地址
        options.add_argument("--proxy-bypass-list=localhost;127.0.0.1")

    return webdriver.Chrome(service=service, options=options)

def main():
    driver = get_driver()
    channels = {'lhtv01': 'litv-longturn01'} # 先只测一个，节省时间
    
    try:
        # --- 诊断步骤 1: 查 IP ---
        logger.info("🕵️ 正在检查当前 IP...")
        try:
            driver.get("https://api.ipify.org?format=json")
            time.sleep(2)
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"🌍 当前浏览器 IP: {page_text}")
        except Exception as e:
            logger.error(f"⚠️ 无法查询 IP: {e}")

        # --- 诊断步骤 2: 访问目标网站 ---
        for cid, slug in channels.items():
            logger.info(f"🔍 正在尝试抓取: {cid}")
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            driver.get(url)
            time.sleep(10) 
            
            # 打印页面标题，看看到底打开了什么
            title = driver.title
            logger.info(f"📄 页面标题是: [{title}]")
            
            # 如果标题包含 403 或 Error，直接报警
            if "403" in title or "Error" in title or "Access Denied" in page_text:
                logger.error("⛔ 访问被拒绝！代理可能未生效或 IP 非台湾。")
            
            html = driver.page_source
            match = re.search(r'["\']assetId["\']\s*:\s*["\']([^"\']{10,})["\']', html)
            
            if match:
                logger.info(f"✅ 居然成功了: {match.group(1)}")
            else:
                logger.warning(f"❌ 依然失败")
                # 打印一部分源码看看结构
                logger.info(f"📝 页面源码前200字符: {html[:200]}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
