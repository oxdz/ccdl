from __future__ import annotations

import logging
import os
import re
import time
from io import BytesIO

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from .utils import (
    ComicLinkInfo,
    ComicReader,
    ProgressBar,
    SiteReaderLoader,
    cc_mkdir,
    get_blob_content,
)

logger = logging.getLogger(__name__)

# 页面元素加载的最大等待时间
WAIT_TIME = 90


class N21:
    """docstring."""

    def __init__(self, dirpath) -> None:
        super().__init__()
        if dirpath[:-1] in ("\\", "/"):
            self._dirpath = dirpath
        else:
            self._dirpath = dirpath + "/"
        try:
            os.makedirs(self._dirpath + "target/")
        except Exception:
            pass

    def edge_connection_offset(self, imgs_split_3_pages):
        """:param imgs_split_3_pages: [[img0_0, img0_1, img_0_2], ...]
        :return: (offset_1, offset_2)
        :rtype: tuple
        """

        def calculate_similarity(a, b):
            count = 0
            img_xor = np.logical_xor(a, b)
            for z in img_xor:
                for x in z:
                    if not x:
                        count += 1
                    else:
                        count -= 1
            return count / img_xor.size

        ij = [[], []]
        for page in imgs_split_3_pages:
            for x in range(2):
                img_ = []
                for offset in range(3, 18):
                    img_.append(
                        np.array(
                            page[x]
                            .crop(
                                (
                                    0,
                                    page[x].height - offset,
                                    page[x].width,
                                    page[x].height - offset + 3,
                                ),
                            )
                            .convert("1"),
                        ),
                    )
                b = np.array(page[x + 1].crop((0, 0, page[1].width, 3)).convert("1"))
                score = [(i + 3, calculate_similarity(img_[i], b)) for i in range(len(img_))]
                score.sort(key=lambda x: x[1], reverse=True)
                ij[x].append(score[0][0])

        offset = [None, None]
        for i in range(2):
            max_count = 0
            for x in list(set(ij[i])):
                if max_count < ij[i].count(x):
                    max_count = ij[i].count(x)
                    offset[i] = x

        return tuple(offset)

    def crop_paste(self, img_chunks, i, j):
        """:param img_chunks: [img_c0, img_c1, img0_c2],
        :returns: An ~PIL.Image.Image object.
        """
        img_new = Image.new(
            "RGB",
            (
                img_chunks[0].width,
                (img_chunks[0].height + img_chunks[1].height + img_chunks[2].height - i - j),
            ),
        )
        img_new.paste(img_chunks[0], (0, 0))
        img_new.paste(img_chunks[1], (0, img_chunks[0].height - i))
        img_new.paste(
            img_chunks[2],
            (0, img_chunks[0].height - i + img_chunks[1].height - j),
        )
        return img_new

    def run(self, imgs, index):
        img_new = self.crop_paste(imgs, *self.edge_connection_offset([imgs]))
        img_new.save(self._dirpath + f"target/{index}.png")


def gen_file_path(link_info: ComicLinkInfo, driver: webdriver.Chrome):
    if link_info.site_name == "www.cmoa.jp":
        try:
            elem = WebDriverWait(driver, WAIT_TIME, 0.5).until(
                lambda x: x.find_element_by_xpath("/html/head/title"),
                message="無法定位元素 " + "/html/head/title",
            )
        except TimeoutException as e:
            logger.error('Find element by xpath("/html/head/title"): ' + str(e))
            raise e
        match = re.search(r"[\w]+_[\w]+_([\w]+)", link_info.param[0][0])
        if match:
            return elem.get_attribute("innerText") + "/" + match.groups()[0]
        else:
            logger.error(f"url:{link_info.url}\ncid: {link_info.param[0][0]}")
            raise ValueError("Unusual cid!")

    elif link_info.site_name == "r.binb.jp":
        return f"binb/{int(time.time() * 1000)}"

    elif link_info.site_name == "booklive.jp":
        return f"booklive/{int(time.time() * 1000)}"

    elif link_info.site_name == "takeshobo.co.jp":
        return f"takeshobo/{int(time.time() * 1000)}"

    elif link_info.site_name == "www.comic-valkyrie.com":
        return f"comic-valkyrie/{int(time.time() * 1000)}"

    elif link_info.site_name == "futabanet.jp":
        return f"futabanet/{int(time.time() * 1000)}"

    elif link_info.site_name == "comic-polaris.jp":
        return f"comic-polaris/{int(time.time() * 1000)}"

    elif link_info.site_name == "www.shonengahosha.co.jp":
        return f"shonengahosha/{int(time.time() * 1000)}"

    elif link_info.site_name == "r-cbs.mangafactory.jp":
        return f"mangafactory/{int(time.time() * 1000)}"

    elif link_info.site_name == "comic-meteor.jp":
        return f"comic-meteor/{int(time.time() * 1000)}"

    #     pass


@SiteReaderLoader.register("binb")
class Binb(ComicReader):
    def __init__(self, link_info: ComicLinkInfo, driver: webdriver.Chrome) -> None:
        super().__init__()
        self._link_info = link_info
        self._driver = driver

    def page_number(self):
        """return [current_page_numb:int, total_numb:int]."""
        page_elem_id = "menu_slidercaption"
        pageNum = []
        count = 180
        while len(pageNum) != 2:
            if count > 0:
                count -= 1
                time.sleep(0.5)
            else:
                raise TimeoutException("")
            try:
                elemt = WebDriverWait(self._driver, WAIT_TIME, 0.5).until(
                    lambda x: x.find_element_by_id(page_elem_id),
                    message="無法定位元素 " + page_elem_id,
                )
            except TimeoutException as e:
                logger.error(str(e))
                raise e
            pageNum = elemt.get_attribute("innerText").split("/")
        pageNum[1] = int(pageNum[1])
        if pageNum[0] != "-":
            pageNum[0] = int(pageNum[0])
        else:
            pageNum[0] = pageNum[1]
        return pageNum

    def downloader(self):
        self._driver.get(self._link_info.url)
        WebDriverWait(self._driver, WAIT_TIME, 0.5).until(
            lambda x: x.find_element_by_id("content"),
            message="漫画加载超时",
        )
        file_path = "./漫畫/" + gen_file_path(self._link_info, self._driver)
        if cc_mkdir(file_path) != 0:
            return -1
        n21 = N21(file_path)
        while self.page_number()[0] > 1:
            ActionChains(self._driver).send_keys(Keys.RIGHT).perform()
        progress_bar = ProgressBar(self.page_number()[1])
        start_page = 0
        reader_flag = self._link_info.param[1]
        while start_page < self.page_number()[1]:
            for i in range(self.page_number()[0], start_page, -1):
                imgs = []
                for j in range(1, 4):
                    try:
                        blob_url = WebDriverWait(self._driver, WAIT_TIME, 0.5).until(
                            lambda x: x.find_element_by_xpath(
                                '//*[@id="content-p{}"]/div/div[{}]/img'.format(
                                    i - (1 - reader_flag),
                                    j,
                                ),
                            ),
                            message="p" + str(i) + "part" + str(j) + "無法定位",
                        )
                    except TimeoutException as e:
                        logger.error(
                            'Find element by id("/html/head/title"): ' + str(e),
                        )
                        raise e
                    blob_uri = blob_url.get_attribute("src")
                    try:
                        img = Image.open(
                            BytesIO(get_blob_content(self._driver, blob_uri)),
                        )
                        img.save(file_path + f"/source/{i}-{j}.png")
                        imgs.append(img)
                    except Exception as e:
                        logger.error(str(e))
                        raise e
                n21.run(imgs, i)
                start_page += 1
                progress_bar.show(start_page)
            ActionChains(self._driver).send_keys(Keys.LEFT).perform()
