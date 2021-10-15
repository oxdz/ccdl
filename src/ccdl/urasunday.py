import datetime
import logging
import re
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.models import Response

from .utils import (ComicLinkInfo, ComicReader, ProgressBar, RqHeaders, RqProxy, SiteReaderLoader,
                    cc_mkdir)

logger = logging.getLogger(__name__)


@SiteReaderLoader.register("urasunday")
class Urasunday(ComicReader):
    def __init__(self, linkinfo: ComicLinkInfo, driver=None) -> None:
        super().__init__()
        self._linkinfo = linkinfo

    def page_info(self):
        resp = requests.get(url=self._linkinfo._url, headers=RqHeaders(), proxies=RqProxy.get_proxy())
        Response.raise_for_status(resp)
        html_text = resp.text

        manga_title = re.search(
            '<meta property="og:title" content="(.*?)" />', html_text)
        if manga_title:
            manga_title = manga_title.groups()[0]
        else:
            manga_title = str(
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

        img_url_l_str = re.search("const pages = ([\S\s]+?);", html_text)
        if not img_url_l_str:
            raise ValueError("Pages not found")
        img_url_l_str = img_url_l_str.groups()[0]
        src_group = re.findall('(http.+?)(?:\'|\")', img_url_l_str)
        if not src_group:
            raise ValueError("empty url list")

        return src_group, manga_title

    @staticmethod
    def downld_one(url, fpath):
        rq = requests.get("".join(url), proxies=RqProxy.get_proxy())
        if rq.status_code != 200:
            raise ValueError("".join(url))
        with open(fpath, 'wb') as fp:
            fp.write(rq.content)

    def downloader(self):
        base_file_path = './漫畫/'
        pages, manga_title = self.page_info()
        base_file_path += manga_title + '/'
        if cc_mkdir(base_file_path, 1) != 0:
            return -1
        show_bar = ProgressBar(len(pages))
        with ThreadPoolExecutor(max_workers=6) as executor:
            count = 0
            for x in executor.map(self.downld_one, pages, [base_file_path + str(x) + '.jpg' for x in range(len(pages))]):
                count += 1
                show_bar.show(count)

