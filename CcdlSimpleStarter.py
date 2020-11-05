import logging
import os
import platform
import sys
import time

from selenium import webdriver

from ccdl import (Binb2, ComicAction, ComicEarthstar, ComicLinkInfo,
                  ComicWalker, Ganma)

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
        print("\n（序號含*）如需登入請提前在程式啟動的瀏覽器中登入，(**)並加載目標url（任意標籤頁）！\n")
        driver = webdriver.Chrome(executable_path=executable_path)
    else:
        print("\n由於未在程式所在目錄發現chromedriver，部分基於selenium採集的站點（序號含*）將無法進行。")
        print("您可於 http://npm.taobao.org/mirrors/chromedriver/ 下載\n")
    
    print("Supported sites:\n")

    print("    1. r.binb.jp/epm/([\w_]+)/")
    print("  **2. www.cmoa.jp/bib/speedreader/speed.html\?cid=([\w-]+)&u0=(\d)&u1=(\d)")
    print()
    print("    3. ganma.jp/xx/xx-xx-xx-xx.../...")
    print()
    print("    4. comic-action.com/episode/([\w-]*)")
    print("   *5. comic-days.com/episode/([\w-]*)")
    print("   *6. comic-gardo.com/episode/([\w-]*)")
    print("    7. comic-zenon.com/episode/([\w-]*)")
    print("    8. comicborder.com/episode/([\w-]*)")
    print("    9. kuragebunch.com/episode/([\w-]*)")
    print("   10. magcomi.com/episode/([\w-]*)")
    print("  *11. pocket.shonenmagazine.com/episode/([\w-]*)")
    print("  *12. shonenjumpplus.com/episode/([\w-]*)")
    print("   13. tonarinoyj.jp/episode/([\w-]*)")
    print("   14. viewer.heros-web.com/episode/([\w-]*)")
    print()
    print("   15. viewer.comic-earthstar.jp/viewer.html?cid=([\w-]*)")
    print()
    print("   16. https://comic-walker.com/viewer/?...&cid=([\w-]*)")
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

        if link_info.site_name == "www.cmoa.jp" or link_info.site_name == "r.binb.jp":
            reader = Binb2(link_info, driver)
        elif link_info.site_name == "ganma.jp":
            reader = Ganma(link_info, None)
        elif link_info.reader == "comic_action":
            reader = ComicAction(link_info, driver)
        elif link_info.reader == "comic_earthstar":
            reader = ComicEarthstar(link_info, driver)
        elif link_info.reader == "comic_walker":
            reader = ComicWalker(link_info, None)
        else:
            print("not supported")
            sys.exit()

        try:
            reader.downloader()
        except Exception as e:
            logger.warning("下載失敗! " + str(e))
            print("下載失敗! " + str(e))
