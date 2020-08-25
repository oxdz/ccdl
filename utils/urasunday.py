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


def get_image(driver: webdriver.Chrome, url: str):
    try:
        driver.get(url)
        pages = driver.execute_script('return pages')
        file_path = "urasunday/" + \
            re.search(r'/([0-9a-zA-Z_]*)/[0-9]*\.webp',
                      pages[0]['src']).group(1)
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
                img = Image.open(BytesIO(content))
                name_img = file_path + "/" + \
                    re.search(r'([0-9]*)\.webp', x['src']).group(1)+'.jpg'
                img.save(name_img, 'JPEG')
                show_bar.show(page_count)
                page_count += 1
        print('下載完成！\n')
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1


if __name__ == "__main__":
    driver = webdriver.Chrome()
    get_image(driver, 'https://urasunday.com/title/86/112536')
