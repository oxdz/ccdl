from __future__ import annotations

import base64
import copy
import json
import logging
import math
import traceback
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import Any

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from .utils import (
    ComicLinkInfo,
    ComicReader,
    ProgressBar,
    RqHeaders,
    RqProxy,
    SiteReaderLoader,
    cc_mkdir,
    draw_image,
    win_char_replace,
)

logger = logging.getLogger("comic-action")

WAIT_TIME = 60


class proc_img_co:
    def __init__(self, width, height):
        self.DIVIDE_NUM = 4
        self.MULTIPLE = 8
        self.width = width
        self.height = height
        self.cell_width = (
            math.floor(self.width / (self.DIVIDE_NUM * self.MULTIPLE)) * self.MULTIPLE
        )
        self.cell_height = (
            math.floor(self.height / (self.DIVIDE_NUM * self.MULTIPLE)) * self.MULTIPLE
        )

    def n21(self, img0) -> Image.Image:
        img_copy = copy.deepcopy(img0)
        for n in range(self.DIVIDE_NUM * self.DIVIDE_NUM):
            src_x = n % self.DIVIDE_NUM * self.cell_width
            src_y = math.floor(n / self.DIVIDE_NUM) * self.cell_height
            i = n % self.DIVIDE_NUM * self.DIVIDE_NUM + math.floor(n / self.DIVIDE_NUM)
            t_x = i % self.DIVIDE_NUM * self.cell_width
            t_y = math.floor(i / self.DIVIDE_NUM) * self.cell_height
            draw_image(
                img0,
                img_copy,
                src_x,
                src_y,
                self.cell_width,
                self.cell_height,
                t_x,
                t_y,
            )
        return img_copy


class proc_img_co_corona:
    def __init__(self, width, height, token: str):
        self.s = width
        self.c = height
        r = []
        token = base64.b64decode(token).decode()
        for x in token:
            r.append(ord(x))

        self.a = r[2:]
        self.i = r[0]
        o = r[1]
        self.u = self.i * o
        self.l = math.floor((self.s - self.s % 8) / self.i)
        self.f = math.floor((self.c - self.c % 8) / o)

    def n21(self, img0) -> Image.Image:
        img_copy = copy.deepcopy(img0)
        for n in range(self.u):
            h = self.a[n]
            p = h % self.i
            m = math.floor(h / self.i)
            g = n % self.i
            v = math.floor(n / self.i)

            draw_image(
                img0,
                img_copy,
                p * self.l,
                m * self.f,
                self.l,
                self.f,
                g * self.l,
                v * self.f,
            )
        return img_copy


@SiteReaderLoader.register("comic_action")
class ComicAction(ComicReader):
    def __init__(self, linkinfo: ComicLinkInfo, driver: webdriver.Chrome):
        super().__init__()
        self._linkinfo = linkinfo
        self._driver = driver

    @staticmethod
    def get_comic_json(linkinfo: ComicLinkInfo, driver: WebDriver = None):
        r""" """
        comic_json: dict[str, Any] = {
            "title": None,
            "subtitle": None,
            "pages": [],
        }
        if linkinfo.param[1] == 1 and driver:
            driver.get(linkinfo.url)
            elem = WebDriverWait(driver, WAIT_TIME, 0.5).until(
                lambda x: x.find_element_by_id("episode-json"),
                message="無法定位元素 episode-json" + ", 獲取json對象數據失敗",
            )
            try:
                json_dataValue = elem.get_attribute("data-value")
                json_dataValue = json.loads(json_dataValue)
            except Exception as e:
                logger.error(traceback.format_exc())
                logger.error(elem)
                raise e
        elif linkinfo.param[1] == 0:
            json_url = linkinfo.url + ".json"
            if linkinfo.site_name in {"to-corona-ex.com", "ichijin-plus.com"}:
                json_url = "https://api.{0}/episodes/{1}/begin_reading".format(
                    linkinfo.site_name, linkinfo.param[0][0]
                )
            rq = requests.get(
                json_url, headers=RqHeaders(), proxies=RqProxy.get_proxy()
            )
            if rq.status_code != 200:
                raise ValueError(json_url)
            json_dataValue = rq.json()
        else:
            raise ValueError(
                "linkinfo.param[1] not 1 or 0, or without driver:" + linkinfo.site_name
            )

        if linkinfo.site_name in {"to-corona-ex.com", "ichijin-plus.com"}:
            ...
            comic_json["subtitle"] = json_dataValue["episode_title"]
            comic_json["title"] = json_dataValue["comic_title"]
            for page in json_dataValue["pages"]:
                if "page_image_url" in page:
                    comic_json["pages"].append(
                        {"src": page["page_image_url"], "drm_hash": page["drm_hash"]}
                    )
        else:
            comic_json["subtitle"] = json_dataValue["readableProduct"]["title"].replace(
                "?", "？"
            )
            comic_json["title"] = json_dataValue["readableProduct"]["series"][
                "title"
            ].replace("?", "？")
            for page in json_dataValue["readableProduct"]["pageStructure"]["pages"]:
                if "src" in page:
                    comic_json["pages"].append(page)

        return comic_json

    @staticmethod
    def gen_url(comic_json: dict):
        for x in comic_json["pages"]:
            yield x["src"]

    @staticmethod
    def gen_token(comic_json: dict):
        for page in comic_json["pages"]:
            if "drm_hash" in page:
                yield page["drm_hash"]
            else:
                yield ""

    @staticmethod
    def gen_sitename(comic_json, sitename):
        for _ in comic_json["pages"]:
            yield sitename

    @staticmethod
    def gen_fpth(comic_json: dict):
        bpth = "./漫畫/" + "/".join(
            (
                win_char_replace(comic_json["title"]),
                win_char_replace(comic_json["subtitle"]),
            )
        )
        count = 0
        for x in range(len(comic_json["pages"])):
            count += 1
            yield [bpth, "{}.png".format(count)]

    @staticmethod
    def downld_one(url, fpth, site_name, token, cookies=None) -> None:
        r"""
        :fpth: [basepath, fname]
        """
        rq = requests.get(url, headers=RqHeaders(), proxies=RqProxy.get_proxy())
        if rq.status_code != 200:
            raise ValueError(url)
        content = rq.content
        img0 = Image.open(BytesIO(content))

        # 源图像
        img0.save(fpth[0] + "/source/" + fpth[1])

        # 复原
        if site_name in {"to-corona-ex.com", "ichijin-plus.com"}:
            proc_img_co_corona(img0.width, img0.height, token).n21(img0=img0).save(
                fpth[0] + "/target/" + fpth[1]
            )
        else:
            proc_img_co(img0.width, img0.height).n21(img0=img0).save(
                fpth[0] + "/target/" + fpth[1]
            )

    def downloader(self) -> None:
        # https://<domain: comic-action.com ...>/episode/13933686331648942300
        comic_json = self.get_comic_json(self._linkinfo, self._driver)
        comic_json["title"]
        total_pages = len(comic_json["pages"])
        cc_mkdir(
            "./漫畫/"
            + "/".join(
                (
                    win_char_replace(comic_json["title"]),
                    win_char_replace(comic_json["subtitle"]),
                )
            )
        )
        show_bar = ProgressBar(total_pages)
        with ThreadPoolExecutor(max_workers=4) as executor:
            count = 0
            for x in executor.map(
                self.downld_one,
                self.gen_url(comic_json),
                self.gen_fpth(comic_json),
                self.gen_sitename(comic_json, self._linkinfo.site_name),
                self.gen_token(comic_json),
            ):
                count += 1
                show_bar.show(count)


# if __name__ == "__main__":
#     url = "https://comic-action.com/episode/13933686331648942300"
#     driver = webdriver.Chrome()
#     ComicAction().downloader(driver, ComicLinkInfo(url))
