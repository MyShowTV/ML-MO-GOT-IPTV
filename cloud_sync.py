import os, re, time, requests
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

def test_proxy():
    print("🌐 正在验证代理是否可用...")
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    try:
        # 增加 timeout 防止卡死
        ip = requests.get("https://ifconfig.me", proxies=proxies, timeout=10).text.strip()
        print(f"✅ 当前出口 IP: {ip}")
        return True
    except Exception as e:
        print(f"❌ 代理不可用: {e}")
        return False

def get_asset_id_advanced(cid, slug, retries=2):
    print(f"\n🔍 正在探测频道: {cid} ({slug}) ...")
    chromedriver_autoinstaller.install()

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    # 模拟更真实的浏览器指纹
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    sw_options = {
        'proxy': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
            'no_proxy': 'localhost,127.0.0.1' # ⚠️ 关键：防止 Selenium 内部通信被代理拦截
        },
        'verify_ssl': False # 忽略 SSL 错误，提高拦截成功率
    }

    for attempt in range(1, retries + 1):
        driver = None
        try:
            driver = webdriver.Chrome(options=options, seleniumwire_options=sw_options)
            url = f"https://www.ofiii.com/channel/watch/{slug}"
            print(f"🌐 第 {attempt} 次访问 {url}")
            driver.get(url)
            
            # 等待播放器框架加载
            time.sleep(12)
            # 模拟真实点击触发播放请求
            driver.execute_script("document.querySelector('body').click();")

            print("⏳ 正在实时扫描 .m3u8 数据序列...")
            # 延长监听时间，确保获取到子播放列表
            time.sleep(15)

            # 逆序搜索，最新的请求（通常是包含 key 的子流链接）在最后
            for request in reversed(driver.requests):
                if request.response:
                    full_url = request.url
                    # --- 核心优化逻辑区 ---
                    # 匹配包含 longturn 且以 .m3u8 结尾的链接
                    if 'longturn' in full_url and '.m3u8' in full_url:
                        # 1. 先提取文件名部分（去掉路径和参数）
                        file_name = full_url.split('/')[-1].split('?')[0]
                        
                        # 2. 针对你提供的格式进行二次验证
                        # 匹配格式如：litv-longturn03-avc1-736000=3-mp4a-114000=2.m3u8
                        if 'avc1' in file_name or 'mp4a' in file_name:
                            aid = file_name.replace('.m3u8', '')
                            print(f"🎯 成功匹配目标链接: {file_name}")
                            print(f"✨ 提取密钥: {aid}")
                            return aid
                            
            print(f"⚠️ 未捕获到符合 longturn 格式的数据包（第 {attempt} 次）")
        except Exception as e:
            print(f"🔥 {cid} 抓取出错（第 {attempt} 次）: {e}")
        finally:
            if driver: driver.quit()
        time.sleep(5)
    
    print(f"❌ {cid} 抓取失败（尝试了 {retries} 次）")
    return None

def main():
    if not test_proxy():
        print("🚫 代理无效，请检查 Mihomo 是否正常运行。")
        return

    channels = {
        'lhtv01': 'litv-longturn03',
        'lhtv02': 'litv-longturn21',
        'lhtv03': 'litv-longturn18',
        'lhtv04': 'litv-longturn11',
        'lhtv05': 'litv-longturn12',
        'lhtv06': 'litv-longturn01',
        'lhtv07': 'litv-longturn02'
    }

    worker_path = "workers.js"
    if not os.path.exists(worker_path):
        print(f"❌ 找不到文件: {worker_path}")
        return

    with open(worker_path, "r", encoding="utf-8") as f:
        content = f.read()

    updated_count = 0
    for cid, slug in channels.items():
        aid = get_asset_id_advanced(cid, slug)
        if aid:
            # 兼容单引号和双引号的正则
            pattern = rf'"{cid}"\s*:\s*\{{.*?key\s*:\s*["\'][^"\']*["\']'
            replacement = f'"{cid}": {{ name: "", key: "{aid}" }}'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            updated_count += 1
        time.sleep(2)

    if updated_count > 0:
        with open(worker_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 成功更新 {updated_count} 个频道密钥至 workers.js")
    else:
        print("⚠️ 任务结束，未更新任何密钥。")

if __name__ == "__main__":
    main()
