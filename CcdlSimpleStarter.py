import logging
import os
import platform
import sys
import time
import traceback

from selenium import webdriver

from ccdl import (Binb2, ComicAction, ComicEarthstar, ComicLinkInfo,
                  ComicWalker, Ganma)
from ccdl.utils import SiteReaderLoad

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
    driver = None
    is_exist = os.path.exists(executable_path)
    print("\n源碼: https://github.com/vircoys/ccdl")
    if is_exist:
        print("\n如需登入（含*）請提前在程式啟動的瀏覽器中登入，並加載目標url（任意標籤頁）！\n")
        driver = webdriver.Chrome(executable_path=executable_path)
    else:
        print("\n由於未在程式所在目錄發現chromedriver，部分基於selenium採集的站點將無法進行。")
        print("您可於 http://npm.taobao.org/mirrors/chromedriver/ 下載\n")

    print("\n>>>>>>>>輸入exit退出<<<<<<<<\n")

    while True:
        url = input("url: ")

        if url == 'exit':
            print('Bye~')
            time.sleep(0.5)
            if driver:
                driver.quit()
            sys.exit()

        link_info = ComicLinkInfo(url)

        Reader = SiteReaderLoad.reader_cls(link_info.reader_name)
        if Reader:
            reader = Reader(link_info, driver)
        else:
            print("not supported")
            continue

        try:
            reader.downloader()
        except Exception as e:
            logger.error(traceback.format_exc())
            print("下載失敗! \n" + traceback.format_exc()) 
