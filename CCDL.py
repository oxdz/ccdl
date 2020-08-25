import logging
import os
import platform
import re
import sys
import time

from selenium import webdriver

from utils.sites_list import sites_list
from utils import ( binb, booklive, comic_days, comic_action, 
                    comic_earthstar, comic_walker,
                    ganganonline, kuragebunch, magcomi, 
                    manga_doa, urasunday, shonenjumpplus, 
                    shonenmagazine, sukima, sunday_webry)

if not os.path.exists("log"):
    os.makedirs("log")

# logger
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


print("*如果需要登錄請在輸入url之前完成登錄（功能未測試）")
print('瀏覽器啓動中...')

time.sleep(2)

# 实例化webdriver对象（Firefox or Chrome）
driver = webdriver.Chrome(executable_path=executable_path)

print("多次嘗試仍失敗時，請將日誌({})發送給維護人員".format(log_file_path))
print("輸入url回車后即可下載當前一話漫畫，輸入exit退出程序。")
print("當前支持的url(正则)為:")

for x in sites_list:
    for y in sites_list[x]:
        print("\t{}".format(y))

while (True):
    try:
        print('url:')
        input_ = input()
        if input_ == 'exit':
            print('Bye~')
            time.sleep(0.5)
            driver.quit()
            sys.exit()
        else:
            match_flag = False
            for x in sites_list:
                for site in sites_list[x]:
                    match = re.search(site, input_)
                    if match != None:
                        if x == "binb_model_1":
                            file_path = sites_list[x][site](match)
                            binb.get_image(driver, input_, file_path, 1)
                        elif x == "binb_model_0":
                            file_path = sites_list[x][site](match)
                            binb.get_image(driver, input_, file_path, 0)
                        else:
                            locals()[x].get_image(driver, input_)
                        match_flag = True
                        break
                if match_flag:
                    break
            if not match_flag:
                print("url解析失败!")
    except Exception as e:
        print('\n')
        print(e)
        logger.error(e)
        try:
            if not os.path.exists("page_source"):
                os.makedirs("page_source")
            with open('page_source' + str(time.time())+'.html') as fp:
                fp.write(driver.page_source)
        except:
            pass
        driver.quit()
        print('\n程序出現異常，請將錯誤信息截圖保存后重啓本程序, 日誌檔位於: {}'.format(log_file_path))
        time.sleep(1000)
        sys.exit()
