import logging
import os
import platform
import sys
import time
from os import system

from ccdl import Binb, ComicLinkInfo
from selenium import webdriver

from ccdl import binb

if not os.path.exists("log"):
    os.makedirs("log")

log_file_path = "log/{}.log".format(time.strftime("%Y-%m-%d"))
fh = logging.FileHandler(filename=log_file_path, encoding="UTF-8")
logging.basicConfig(
    handlers=[fh], format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CCDL")

if 'Linux' in platform.platform().split('-'):
    executable_path = './chromedriver'
elif 'Windows' in platform.platform().split('-'):
    executable_path = './chromedriver.exe'
else:
    logger.error("platform not win or linux")
    raise ValueError("os")

if __name__ == "__main__":
    driver = webdriver.Chrome(executable_path=executable_path)
    print("\n如需登入請提前在程式啟動的瀏覽器中登入！\n")
    print("Supported sites:\n")
    print("    1. www.cmoa.jp/bib/speedreader/speed.html\?cid=([0-9a-zA-Z_]+)")
    print("\n>>>>>>>>輸入exit退出<<<<<<<<\n")
    while True:
        url = input("url: ")
        if url == 'exit':
            print('Bye~')
            time.sleep(0.5)
            driver.quit()
            sys.exit()
        link_info = ComicLinkInfo(url)
        if link_info.site_name == "www.cmoa.jp":
            binb = Binb(link_info, driver)
            try:
                binb.downloader()
            except Exception as e:
                logger.warning("下載失敗! " + str(e))