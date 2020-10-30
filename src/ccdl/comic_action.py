import copy
import json
import logging
import math
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

from .utils import ComicLinkInfo, ProgressBar, RqHeaders, cc_mkdir, draw_image

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

    def n21(self, img0) -> Image.Image:
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
    def __init__(self, linkinfo: ComicLinkInfo, driver: webdriver.Chrome):
        super().__init__()
        self._linkinfo = linkinfo
        self._driver = driver

    @staticmethod
    def get_comic_json(driver):
        r"""
        """
        comic_json = {
            "title": None,
            "subtitle": None,
            "pages": [],
        }

        elem = WebDriverWait(driver, WAIT_TIME, 0.5).until(
            lambda x: x.find_element_by_id("episode-json"),
            message="無法定位元素 episode-json" + ", 獲取json對象數據失敗")

        json_dataValue = elem.get_attribute("data-value")
        json_dataValue = json.loads(json_dataValue)

        comic_json["subtitle"] = json_dataValue["readableProduct"]["title"].replace("?", "？")
        comic_json["title"] = json_dataValue["readableProduct"]["series"]["title"].replace("?", "？")
        for page in json_dataValue["readableProduct"]["pageStructure"]["pages"]:
            if "src" in page:
                comic_json["pages"].append(page)
        return comic_json

    @staticmethod
    def gen_url(comic_json: dict):
        for x in comic_json["pages"]:
            yield x["src"]

    @staticmethod
    def gen_fpth(comic_json: dict):
        bpth = "./漫畫/" + \
            "/".join((comic_json["title"], comic_json["subtitle"]))
        count = 0
        for x in range(len(comic_json["pages"])):
            count += 1
            yield [bpth, "{}.png".format(count)]

    @staticmethod
    def downld_one(url, fpth, cookies=None):
        r"""
        :fpth: [basepath, fname]
        """
        rq = requests.get(url, headers=RqHeaders())
        if rq.status_code != 200:
            raise ValueError(url)
        content = rq.content
        img0 = Image.open(BytesIO(content))

        # 源图像
        img0.save(fpth[0] + "/source/" + fpth[1])

        # 复原
        proc = proc_img_co(img0.width, img0.height)
        proc.n21(img0=img0).save(fpth[0] + "/target/" + fpth[1])

    def downloader(self):
        # https://<domain: comic-action.com ...>/episode/13933686331648942300
        self._driver.get(self._linkinfo.url)
        comic_json = ComicAction.get_comic_json(self._driver)
        total_pages = len(comic_json["pages"])
        show_bar = ProgressBar(total_pages)
        cc_mkdir("./漫畫/" + \
            "/".join((comic_json["title"], comic_json["subtitle"])))
        with ThreadPoolExecutor(max_workers=4) as executor:
            count = 0
            for x in executor.map(ComicAction.downld_one,
                                  ComicAction.gen_url(comic_json),
                                  ComicAction.gen_fpth(comic_json)):
                count += 1
                show_bar.show(count)


# if __name__ == "__main__":
#     url = "https://comic-action.com/episode/13933686331648942300"
#     driver = webdriver.Chrome()
#     ComicAction().downloader(driver, ComicLinkInfo(url))
