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

from .utils import ComicLinkInfo, ProgressBar, RqHeaders, draw_image, cc_mkdir

logger = logging.getLogger("comic-action")

WAIT_TIME = 60


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
            draw_image(img0, img_copy, src_x, src_y, self.cell_width,
                       self.cell_height, t_x, t_y)
        return img_copy


class ComicAction(object):
    def __init__(self):
        super().__init__()

    def downloader(self, link_info: ComicLinkInfo, driver: webdriver.Chrome):
        try:
            # https://[domain: comic-action.com ...]/episode/13933686331648942300
            driver.get(link_info.url)

            series_title = WebDriverWait(driver, WAIT_TIME, 0.5).until(
                lambda x: x.find_element_by_class_name("series-header-title"),
                message="解析漫畫名失敗").text

            episode_title = WebDriverWait(driver, WAIT_TIME, 0.5).until(
                lambda x: x.find_element_by_class_name("episode-header-title"),
                message="解析當前一話標題失敗").text

            episode_date = WebDriverWait(driver, WAIT_TIME, 0.5).until(
                lambda x: x.find_element_by_class_name('episode-header-date'),
                message="解析當前一話日期失敗").text

            file_path = "./漫畫/" + \
                '/'.join([series_title, episode_title + ' ' + episode_date])
            if cc_mkdir(file_path) != 0:
                print("下載取消！")
                return 0
            elem = WebDriverWait(driver, WAIT_TIME, 0.5).until(
                lambda x: x.find_element_by_id("episode-json"),
                message="無法定位元素 episode-json" + ", 獲取json對象數據失敗")
            json_dataValue = elem.get_attribute("data-value")
            pages = json.loads(
                json_dataValue)['readableProduct']['pageStructure']['pages']

            page_count = 1
            total_pages = 0
            for i in range(len(pages)):
                if 'src' in pages[i]:
                    total_pages += 1
            show_bar = ProgressBar(total_pages)
            for i in range(len(pages)):
                if 'src' not in pages[i]:
                    continue
                content = requests.get(pages[i]['src'],
                                       headers=RqHeaders()).content
                img0 = Image.open(BytesIO(content))
                img0.save(file_path + "/source/{}.jpg".format(page_count),
                          quality=100)
                proc = proc_img_co(img0.width, img0.height)
                proc.n21(img0=img0).save(file_path +
                                         "/target/{}.jpg".format(page_count),
                                         quality=100)
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
    url = "https://comic-action.com/episode/13933686331648942300"
    driver = webdriver.Chrome()
    ComicAction().downloader(driver, ComicLinkInfo(url))
