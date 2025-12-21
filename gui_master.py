import sys, os, re, time, threading
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, QProgressBar)
from PyQt6.QtCore import pyqtSignal, QObject
import chromedriver_autoinstaller
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CrawlerSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    result = pyqtSignal(str, str)

class OfiiiGuiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.signals = CrawlerSignals()
        self.setWindowTitle('OFIII 动态密匙拦截器 - 视窗完整版')
        self.setGeometry(100, 100, 900, 650)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.btn_start = QPushButton("🚀 开始动态抓取 (本地模式)")
        self.btn_start.setFixedHeight(50)
        self.btn_start.clicked.connect(self.start_thread)
        
        self.pbar = QProgressBar()
        self.log_output = QTextEdit()
        self.log_output.setStyleSheet("background: #000; color: #0f0; font-family: Consolas;")
        
        layout.addWidget(self.btn_start)
        layout.addWidget(self.pbar)
        layout.addWidget(QLabel("控制台实时日志:"))
        layout.addWidget(self.log_output)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.signals.log.connect(lambda m: self.log_output.append(f"[{datetime.now().strftime('%H:%M:%S')}] {m}"))
        self.signals.progress.connect(self.pbar.setValue)

    def start_thread(self):
        self.btn_start.setEnabled(False)
        threading.Thread(target=self.run_crawler, daemon=True).start()

    def run_crawler(self):
        chromedriver_autoinstaller.install()
        # 默认连接本地 Clash 端口 7890
        wire_options = {
            'proxy': {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'},
            'verify_ssl': False
        }
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        
        driver = webdriver.Chrome(seleniumwire_options=wire_options, options=chrome_options)
        channels = {'lhtv01': 'litv-longturn03', 'lhtv02': 'litv-longturn21'}
        
        try:
            for i, (cid, slug) in enumerate(channels.items()):
                self.signals.log.emit(f"正在分析频道: {cid}...")
                driver.get(f"https://www.ofiii.com/channel/watch/{slug}")
                del driver.requests
                
                wait = WebDriverWait(driver, 20)
                btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button")))
                driver.execute_script("arguments[0].click();", btn)
                
                # 嗅探逻辑
                found = False
                for _ in range(20):
                    for req in driver.requests:
                        if req.response and 'playlist' in req.url and 'avc1' in req.url:
                            key = re.search(r'playlist/([a-zA-Z0-9_-]+/[^?#\s]+)', req.url).group(1)
                            self.signals.log.emit(f"🎯 抓获: {key}")
                            found = True; break
                    if found: break
                    time.sleep(2)
                self.signals.progress.emit(int((i+1)/len(channels)*100))
            driver.quit()
        except Exception as e:
            self.signals.log.emit(f"🔥 错误: {str(e)}")
        self.btn_start.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = OfiiiGuiApp()
    ex.show()
    sys.exit(app.exec())
