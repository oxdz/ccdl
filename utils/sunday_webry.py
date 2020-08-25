import logging
import os
import re
import time
from io import BytesIO

import requests
from PIL import Image
from selenium import webdriver
from .common.progress_bar import progress_bar

logger = logging.getLogger(__name__)

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36",
    "accept": "image/webp,image/apng,image/*,*/*;q=0.8",

}

def xor_img(arr_img: list, encryption_hex):
    hex_ = re.findall("(.{1,2})", encryption_hex)
    key_= []
    for x in hex_:
        key_.append(int(x, 16))
    img_ = []
    len_key_ = len(key_)
    for a in range(len(arr_img)):
        img_.append(arr_img[a] ^ key_[a % len_key_])
    return img_

def write2jpg(file_path, img_, pageNumber):
    with open(file_path+'/'+ str(pageNumber) +'.jpg', 'wb') as fp:
        for x in img_:
            fp.write((x).to_bytes(length=1, byteorder='big'))

def get_image(driver: webdriver.Chrome, url: str):
    try:
        driver.get(url)
        pages = driver.execute_script('return pages')
        
        file_path = "sunday-webry/" + \
                driver.find_element_by_css_selector('div.header-wrapper-label').text
        
        if os.path.exists(file_path):
            print('\n當前一話的文件夾{}存在，繼續運行數據將被覆蓋，'.format(file_path))
            print('是否繼續運行？（y/n）')
            yn = input()
            if yn == 'y' or yn == 'yes' or yn == 'Y':
                print('開始下載...') 
            else:
                return -1
        else:
            os.makedirs(file_path)
            print('創建文件夾'+file_path)
            print('開始下載...')

        page_count = 1
        total_pages = 0
        for x in pages:
            if 'src' in x:
                total_pages += 1
        show_bar = progress_bar(total_pages)
        for x in pages:
            if 'src' in x:
                for t5 in range(5):
                    try:
                        content = requests.get(
                            x['src'], headers=headers).content
                        break
                    except Exception as e:
                        logger.warning(e)
                        time.sleep(5)
                    raise Exception('下載失敗，請檢查網絡或聯係開發者')
                img_ = xor_img(content, x['encryption_hex'])
                write2jpg(file_path, img_, x['pageNumber'])
                show_bar.show(page_count)
                page_count += 1
        print('下載完成！\n')
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1


if __name__ == "__main__":
    driver = webdriver.Chrome(executable_path="./chromedriver")
    get_image(driver, "https://www.sunday-webry.com/viewer.php?chapter_id=27811")