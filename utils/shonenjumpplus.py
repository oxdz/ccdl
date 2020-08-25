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
from selenium.webdriver.support.wait import WebDriverWait
from .common.progress_bar import progress_bar

logger = logging.getLogger(__name__)

WAIT_TIME = 60

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"
}


def drawImage(img0, img_copy, src_x, src_y, swidth, sheight, x, y, width=None, height=None):
    img_copy.paste(
        img0.crop
        (
            (src_x, src_y, src_x + swidth, src_y + sheight),
        ),
        (x, y)
    )


class proc_img_co:
    def __init__(self, width, height):
        self.DIVIDE_NUM = 4
        self.MULTIPLE = 8
        self.width = width
        self.height = height
        self.cell_width = math.floor(
            self.width / (self.DIVIDE_NUM * self.MULTIPLE)) * self.MULTIPLE
        self.cell_height = math.floor(
            self.height / (self.DIVIDE_NUM * self.MULTIPLE)) * self.MULTIPLE

    def n21(self, img0):
        img_copy = copy.deepcopy(img0)
        for n in range(self.DIVIDE_NUM * self.DIVIDE_NUM):
            src_x = n % self.DIVIDE_NUM * self.cell_width
            src_y = math.floor(n / self.DIVIDE_NUM) * self.cell_height
            i = n % self.DIVIDE_NUM * self.DIVIDE_NUM + \
                math.floor(n / self.DIVIDE_NUM)
            t_x = i % self.DIVIDE_NUM * self.cell_width
            t_y = math.floor(i / self.DIVIDE_NUM) * self.cell_height
            drawImage(img0, img_copy, src_x, src_y,
                      self.cell_width, self.cell_height, t_x, t_y)
        return img_copy


def get_image(driver: webdriver.Chrome, url: str):
    try:
        # https://shonenjumpplus.com/episode/13933686331654870520
        file_path = "shonenjumpplus/" + \
            re.search('episode/([0-9a-zA-Z_-]*)', url).group(1)
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
        driver.get(url)
        elem = WebDriverWait(driver, WAIT_TIME, 0.5).until(
            lambda x: x.find_element_by_id("episode-json"),
            message="無法定位元素 episode-json" + ", 獲取json對象數據失敗"
        )
        json_dataValue = elem.get_attribute("data-value")
        pages = json.loads(json_dataValue)[
            'readableProduct']['pageStructure']['pages']

        page_count = 1
        total_pages = 0
        for i in range(len(pages)):
            if 'src' in pages[i]:
                total_pages += 1
        show_bar = progress_bar(total_pages)

        for i in range(len(pages)):
            if 'src' not in pages[i]:
                continue
            content = requests.get(pages[i]['src'], headers=headers).content
            img0 = Image.open(BytesIO(content))
            img0.save(file_path+"/source/{}.jpg".format(page_count))
            proc = proc_img_co(img0.width, img0.height)
            proc.n21(img0=img0).save(
                file_path+"/target/{}.jpg".format(page_count))
            show_bar.show(page_count)
            page_count = page_count + 1
            if "contentEnd" in pages[i]:
                print('下載完成！\n')
                break
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1


if __name__ == "__main__":
    url = "https://shonenjumpplus.com/episode/13933686331654870520"
    driver = webdriver.Chrome()
    get_image(driver, url)
