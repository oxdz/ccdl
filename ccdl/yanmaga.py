import asyncio
import json
import logging
import os
import re
from io import BytesIO

import requests
from aiohttp.client import ClientSession
from PIL import Image
from selenium import webdriver
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
)

API_URL_ComicInfo = "https://api2-yanmaga.comici.jp/book/Info?comici-viewer-id={}"
API_URL_EpisodeInfo = (
    "https://api2-yanmaga.comici.jp/book/episodeInfo?comici-viewer-id={}"
)
API_URL_ContentsInfo = (
    "https://api2-yanmaga.comici.jp/book/contentsInfo?user-id={}"
    "&comici-viewer-id={}&page-from={}&page-to={}"
)

logger = logging.getLogger(__name__)
headers = RqHeaders()
headers["referer"] = "https://yanmaga.jp/"
WAIT_TIME = 60


@SiteReaderLoader.register("yanmaga")
class Yanmaga(ComicReader):
    def __init__(
        self, link_info: ComicLinkInfo, driver: webdriver.Chrome = None
    ) -> None:
        super().__init__()
        self._link_info = link_info
        self._driver = driver

    def get_comic_user_and_viewer_id(self, url: str):
        """
        :param: url
        :returns: user_id, view_id
        """
        if not re.match(r"https://yanmaga.jp/comics/(.+?)/[\w]+", url):
            raise ValueError("unsupported url: {}".format(url))
        self._driver.get(url)
        elem = WebDriverWait(self._driver, WAIT_TIME, 0.5).until(
            lambda x: x.find_element_by_id("comici-viewer"),
            message="無法定位元素 comici-viewer" + ", 獲取comici-viewer失敗",
        )
        view_id = elem.get_attribute("comici-viewer-id")
        user_id = elem.get_attribute("data-member-jwt")
        return user_id, view_id

    def get_comic_title(self, view_id):
        """
        :param view_id:
        :returns: title
        """
        rq = requests.get(
            url=API_URL_ComicInfo.format(view_id),
            headers=headers,
            proxies=RqProxy.get_proxy(),
        )
        return rq.json().get("result").get("title")

    def get_episode_info(self, view_id):
        """
        :param view_id:
        :returns: {
            'id': {
                'page_count': int,
                'name: str
            }
        }
        """
        rq = requests.get(
            url=API_URL_EpisodeInfo.format(view_id),
            headers=headers,
            proxies=RqProxy.get_proxy(),
        )
        result = rq.json().get("result")
        epinfo = {}
        for r in result:
            epinfo[r.get("id")] = {
                "page_count": int(r.get("page_count")),
                "name": r.get("name"),
            }
        return epinfo

    def get_content_info(self, user_id, view_id, page_to: int, page_from=0):
        rq = requests.get(
            API_URL_ContentsInfo.format(user_id, view_id, page_from, page_to),
            headers=headers,
            proxies=RqProxy.get_proxy(),
        )
        result = rq.json().get("result")

        urls = []
        scrambles = []
        sizes = []
        for x in result:
            urls.append(x.get("imageUrl"))
            scrambles.append(json.loads(x.get("scramble")))
            sizes.append((x.get("width"), x.get("height")))
        return urls, scrambles, sizes

    def decode_image(self, img: Image.Image, scramble: list):
        target = img.copy()
        h = img.height // 4
        w = img.width // 4

        for img_scc in range(len(scramble)):
            y = img_scc % 4 * h
            x = img_scc // 4 * w if img_scc >= 4 else 0
            src_y = scramble[img_scc] % 4 * h
            src_x = scramble[img_scc] // 4 * w if scramble[img_scc] >= 4 else 0
            draw_image(img, target, src_x, src_y, w, h, x, y)
        return target

    @classmethod
    def downld_images(cls, url: list, headers=None, cookies=None, bar=None):
        """
        :param url: 所有图片的url
        :param fp: 处理后的图像存储路径
        :param s_fp: 原始下载的图像的存储路径, default None
        :param headers:  (list, tuple) for each || dict for all
        :param cookies:  (list, tuple) for each || dict for all
        :returns: {url: bstr if success else None}
        """

        async def dl_img(url, headers=None, cookies=None):
            nonlocal bar
            async with ClientSession(headers=headers, cookies=cookies) as session:
                async with session.get(url=url) as response:
                    r = (url, await response.content.read())
                    bar.show() if bar else None
                    return r

        fs = []
        for x in range(len(url)):
            h = headers[x] if isinstance(headers, (list, tuple)) else headers
            c = cookies[x] if isinstance(cookies, (list, tuple)) else cookies
            fs.append(asyncio.ensure_future(dl_img(url[x], headers=h, cookies=c)))
        loop = asyncio.get_event_loop()
        done, pedding = loop.run_until_complete(asyncio.wait(fs))
        result = []
        for r in done:
            try:
                if isinstance(r.result(), tuple):
                    result.append(r.result())
            except Exception:
                pass
        result = dict(result)
        rt = {}
        for u in url:
            rt[u] = result.get(u)
        return rt

    def downloader(self):
        user_id, view_id = self.get_comic_user_and_viewer_id(self._link_info.url)
        title = self.get_comic_title(view_id)
        episode_info = self.get_episode_info(view_id).get(view_id)
        sub_title = episode_info.get("name")
        page_count = episode_info.get("page_count")
        bpath = os.path.join("./漫畫/", title, sub_title)
        if cc_mkdir(bpath, 1) != 0:
            return -1
        urls, scrambles, sizes = self.get_content_info(
            user_id, view_id, page_to=page_count - 1
        )
        bar = ProgressBar(page_count)
        print("Downloading：")
        imgs = self.downld_images(urls, headers=headers, bar=bar)
        print("Decoding:")
        bar = ProgressBar(page_count)
        for x in range(len(urls)):
            img = Image.open(BytesIO(imgs[urls[x]]))
            path = os.path.join(bpath, str(x + 1).zfill(3) + ".png")
            self.decode_image(img, scrambles[x]).save(path)
            bar.show()
        print("Finished!")


# if __name__ == '__main__':
#     # comici_vid = '4633af6ae1c0d82c123222a20748426b'
#     # url = 'https://yanmaga.jp/comics/恥じらう君が見たいんだ/0cf017ab837eb5f26f8cceef45f7c2c1'
#     # linkinfo = ComicLinkInfo(url)
#     # Yanmaga(linkinfo).downloader()
#     # 找不到当前漫画信息则请求手动输入
#     url = 'https://yanmaga.jp/'
#     linkinfo = ComicLinkInfo(url)
#     Yanmaga(linkinfo).downloader()
