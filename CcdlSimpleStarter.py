import logging
import os
import platform
import sys
import time
import traceback

from selenium import webdriver

from ccdl import (Binb2, ComicAction, ComicEarthstar, ComicLinkInfo,
                  ComicWalker, Ganma)
from ccdl.utils import RqProxy, SiteReaderLoader, get_windwos_proxy

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
    proxy_server = get_windwos_proxy()
    if proxy_server:
        RqProxy.set_proxy(proxy_server, proxy_server)
    del proxy_server
else:
    logger.error("platform not win or linux, may failed")
    executable_path = './chromedriver'
    # raise ValueError("os")
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

if __name__ == "__main__":
    driver = None
    is_exist = os.path.exists(executable_path)
    print("\n源碼: https://github.com/oxdz/ccdl")
    if is_exist:
        print("\n如需登入（含*）請提前在程式啟動的瀏覽器中登入，並加載目標url（任意標籤頁）！\n")
        try:
            driver = webdriver.Chrome(executable_path=executable_path, options=chrome_options)
        except Exception as e:
            logger.error(traceback.format_exc())
            print("Chrome啟動失敗! 請檢查Chrome與chromedriver版本\n" + traceback.format_exc())
            print("您可於 http://npm.taobao.org/mirrors/chromedriver/ 下載\n")

            driver = None
            if input("Do you want to continue? （y/n）") in ('y','Y','YES'):
                pass
            else:
                time.sleep(0.8)
                print("Bye~")
                time.sleep(0.8)

                sys.exit()
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

        reader = SiteReaderLoader(link_info, driver)
        if reader is not None:
            try:
                reader.downloader()
            except Exception as e:
                logger.error(traceback.format_exc())
                print("下載失敗! \n" + traceback.format_exc()) 
        else:
            print("not supported")
            continue
