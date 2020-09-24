import base64
import logging
from operator import delitem
import os
from os import link
import re
from re import match
import time
from io import BytesIO

import numpy as np
from PIL import Image
from numpy.lib.function_base import quantile
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from .utils import ComicLinkInfo, ProgressBar, get_blob_content, cc_mkdir

logger = logging.getLogger(__name__)

# 页面元素加载的最大等待时间
WAIT_TIME = 90


def edge_connection_offset(img_np):
    ij = []
    for x in range(len(img_np) - 1):
        cnt = []
        h = img_np[x].shape[0]
        for y in range(10):
            cnt.append(sum(abs(img_np[x][h - 1] - img_np[x + 1][y])))
        ij.append(cnt.index(max(cnt)) + 1)
    return ij


def gen_file_path(link_info: ComicLinkInfo, driver: webdriver.Chrome):
    if link_info.site_name == "www.cmoa.jp":
        try:
            elem = WebDriverWait(driver, WAIT_TIME, 0.5).until(
                lambda x: x.find_element_by_xpath("/html/head/title"),
                message="無法定位元素 " + "/html/head/title")
        except TimeoutException as e:
            logger.error("Find element by xpath(\"/html/head/title\"): " + str(e))
            raise e
        match = re.search("[\w]+_[\w]+_([\w]+)", link_info.param[0][0])
        if match:
            return elem.get_attribute("innerText") + '/' + match.groups()[0]
        else:
            logger.error("url:{}\ncid: {}".format(link_info.url,
                                                  link_info.param[0][0]))
            raise ValueError("Unusual cid!")

    elif link_info.site_name == "r.binb.jp":
        pass

    elif link_info.site_name == "booklive.jp":
        pass

    elif link_info.site_name == "www.comic-valkyrie.com":
        pass

    elif link_info.site_name == "futabanet.jp":
        pass

    elif link_info.site_name == "comic-polaris.jp":
        pass

    elif link_info.site_name == "www.shonengahosha.co.jp":
        pass
    # elif domain == "":
    #     pass


class Binb(object):
    def __init__(self, link_info: ComicLinkInfo, driver: webdriver.Chrome):
        super().__init__()
        self._link_info = link_info
        self._driver = driver

    def page_number(self):
        """
        return [current_page_numb:int, total_numb:int]
        """
        page_elem_id = 'menu_slidercaption'
        match = re.search("cid=([0-9a-zA-Z_]+)", self._driver.current_url)
        if not match or match.groups()[0] != self._link_info.param[0][0]:
            self._driver.get(self._link_info.url)
        pageNum = []
        count=8
        while len(pageNum) != 2:
            if count > 0:
                count -= 1
                time.sleep(0.35)
            else:
                raise TimeoutException("")
            try:
                elemt = WebDriverWait(self._driver, WAIT_TIME, 0.5).until(
                        lambda x: x.find_element_by_id(page_elem_id),
                        message="無法定位元素 " + page_elem_id
                    )
            except TimeoutException as e:
                logger.error(str(e))
                raise e
            pageNum = elemt.get_attribute('innerText').split('/')
        pageNum[1] = int(pageNum[1])
        if (pageNum[0] != '-'):
            pageNum[0] = int(pageNum[0])
        else:
            pageNum[0] = pageNum[1]
        return pageNum

    def downloader(self):
        # self._driver.get(self._link_info.url)
        self.page_number()
        file_path = "./漫畫/" + gen_file_path(self._link_info, self._driver)
        if cc_mkdir(file_path) != 0:
            return -1
        while(self.page_number()[0] > 1):
            ActionChains(self._driver).send_keys(Keys.RIGHT).perform()
        progress_bar = ProgressBar(self.page_number()[1])
        start_page = 0
        reader_flag = self._link_info.param[1]
        while(start_page < self.page_number()[1]):
            for i in range(self.page_number()[0], start_page, -1):
                imgs = []
                for j in range(1, 3 + 1):
                    try:
                        blob_url = WebDriverWait(self._driver, WAIT_TIME, 0.5).until(
                                lambda x: x.find_element_by_xpath('//*[@id="content-p{}"]/div/div[{}]/img'.format(i-(1-reader_flag), j)),
                                message="p" + str(i) + "part" + str(j) + "無法定位"
                            )
                    except TimeoutException as e:
                        logger.error("Find element by id(\"/html/head/title\"): " + str(e))
                        raise e
                    blob_uri = blob_url.get_attribute('src')
                    try:
                        img = Image.open(BytesIO(get_blob_content(self._driver, blob_uri)))
                        img.save(file_path+'/source/{}-{}.jpg'.format(i, j), quality=100)
                        imgs.append(img)
                    except Exception as e:
                        logger.error(str(e))
                        raise e
                imgs_np = []
                for x in range(len(imgs)):
                    imgs_np.append(np.array(imgs[x].convert('1')).astype(int))
                ij = edge_connection_offset(imgs_np)
                w = 0
                h = 0
                for x in imgs:
                    w += x.size[0]
                    h += x.size[1]
                w = int(w / 3)
                img3t1 = Image.new('RGB', (w, h - 12))
                img3t1.paste(imgs[0], (0, 0))
                img3t1.paste(imgs[1], (0, imgs[0].size[1] - ij[0]))
                img3t1.paste(imgs[2], (0, imgs[0].size[1] + imgs[1].size[1] - ij[0] - ij[1]))
                img3t1.save('./{}/target/{}.jpg'.format(file_path, i), quality=100)
                start_page += 1
                progress_bar.show(start_page)
            ActionChains(self._driver).send_keys(Keys.LEFT).perform()
        print("下載完成!")