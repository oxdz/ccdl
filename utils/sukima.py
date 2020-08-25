import copy
import json
import logging
import math
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
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"
}


def draw_image(img0, img_copy, src_x, src_y, swidth, sheight, x, y, width=None, height=None):

    img_copy.paste(
        img0.crop
        (
            (src_x, src_y, src_x + swidth, src_y + sheight),
        ),
        (x, y)
    )
    return img_copy


def get_image(driver: webdriver.Chrome, url):
    # https://www.sukima.me/bv/t/BT0000435728/v/1/s/1/p/1
    try:
        driver.get(url)
        for x in range(5):
            try:
                volume_id = driver.execute_script("return VOLUME_ID;")
                img_json = driver.execute_script("return PAGES_INFO;")
                block_size = driver.execute_script("return BLOCKLEN;")
                break
            except Exception as e:
                logger.warning(e)
                print(e)
                time.sleep(2)
            logger.error("頁面解析失敗!")
            print('頁面解析失敗!\n')
            return -2

        if img_json == None:
            logger.error("PAGES_INFO（json）解析失敗!")
            print('PAGES_INFO（json）解析失敗!\n')
            return -2

        file_path = "sukima/" + volume_id
        if os.path.exists(file_path+'/source'):
            print('\n當前一話的文件夾{}存在，繼續運行數據將被覆蓋，'.format(file_path))
            print('是否繼續運行？（y/n）')
            yn = input()
            if yn == 'y' or yn == 'yes' or yn == 'Y':
                print('開始下載...')
            else:
                return -1
        else:
            os.makedirs(file_path+'/source')
            if os.path.exists(file_path+'/target') == False:
                os.makedirs(file_path+'/target')

            print('創建文件夾'+file_path)
            print('開始下載...')

        page_count = 1
        total_pages = 0
        for item in img_json:
            if "page_url" in item and "shuffle_map" in item and "page_number" in item:
                total_pages += 1
        show_bar = progress_bar(total_pages)

        for item in img_json:
            if "page_url" in item and "shuffle_map" in item and "page_number" in item:
                content = requests.get(
                    item["page_url"], headers=headers).content
                shuffle_map = json.loads(item["shuffle_map"])
                img0 = Image.open(BytesIO(content))
                xSplitCount = math.floor(img0.width / block_size)
                ySplitCount = math.floor(img0.height / block_size)
                img0.save(
                    file_path+"/source/{}.jpg".format(item["page_number"]))
                img_copy = copy.deepcopy(img0)
                count = 0
                for i in range(xSplitCount):
                    for j in range(ySplitCount):
                        draw_image(
                            img0, img_copy,
                            i*block_size, j*block_size,
                            block_size, block_size,
                            shuffle_map[count][0], shuffle_map[count][1]
                        )
                        count += 1
                img_copy.save(
                    file_path+"/target/{}.jpg".format(item["page_number"]))
                show_bar.show(page_count)
                page_count += 1
        print('下載完成！\n')
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1
    return 0


if __name__ == "__main__":
    driver = webdriver.Chrome()
    #get_image(driver, "https://www.sukima.me/bv/t/futaba0000016/v/1/s/1/p/1")
    get_image(driver, "https://www.sukima.me/bv/t/yurikabe/v/1/s/1/p/1")
