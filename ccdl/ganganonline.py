import json
import logging
import os
import re

import requests
from requests.adapters import HTTPAdapter
from selenium import webdriver

from .utils import (
    ComicLinkInfo,
    ComicReader,
    ProgressBar,
    RqHeaders,
    RqProxy,
    SiteReaderLoader,
    cc_mkdir,
    downld_url,
    win_char_replace,
    write2file,
)

logger = logging.getLogger(__name__)

COMINC_BASE_URL = "https://www.ganganonline.com"


@SiteReaderLoader.register("ganganonline")
class Ganganonline(ComicReader):
    def __init__(
        self, linkinfo: ComicLinkInfo, driver: webdriver.Chrome = None
    ) -> None:
        super().__init__()
        self._linkinfo = linkinfo
        self._driver = driver

        self.rq = requests.session()
        http_adapter = HTTPAdapter(max_retries=5)
        self.rq.mount(prefix="https://", adapter=http_adapter)
        self.rq.mount(prefix="http://", adapter=http_adapter)
        self.rq.headers = RqHeaders()  # type: ignore[assignment]
        proxy = RqProxy.get_proxy()
        if proxy is not None:
            self.rq.proxies = proxy

    def downloader(self):
        r = self.rq.get(self._linkinfo.url)
        if r.status_code != 200:
            logger.error(
                "http code: {} ;ganganonline: {}".format(
                    r.status_code, self._linkinfo.url
                )
            )
            print("failed!")
            return
        index_html = r.content.decode()
        next_data = re.search('id="__NEXT_DATA__.*>(.*)</script>', index_html)
        if next_data:
            next_data = next_data.groups()[0]
        else:
            logger.error(index_html)
            print("failed!")
            return
        comic_data = json.loads(next_data)
        comic_data = comic_data["props"]["pageProps"]["data"]
        base_file_path = "./漫畫/"
        title_name = win_char_replace(comic_data["titleName"])
        chapter_name = win_char_replace(comic_data["chapterName"])
        comic_path = os.path.join(base_file_path, title_name, chapter_name)
        if cc_mkdir(comic_path, 1) != 0:
            return
        url = []
        for x in comic_data["pages"]:
            if "image" in x and "imageUrl" in x["image"]:
                url.append(COMINC_BASE_URL + x["image"]["imageUrl"])
        total_page = len(url)
        bar = ProgressBar(total_page)
        print("Downloading:")
        result = downld_url(
            url=url, bar=bar, headers=self.rq.headers, cookies=self.rq.cookies
        )
        print("Save to file:")
        bar.reset()
        write2file(comic_path, result, total_page, "webp", "png", bar)
        print("下載完成！\n")


# https://www.ganganonline.com/title/1267/chapter/50371
