import json
import logging
import re
import time
from io import BytesIO

import requests
from PIL import Image
from requests.adapters import HTTPAdapter

from ccdl.utils import ProgressBar, cc_mkdir, draw_image

# if __name__ == "__main__":
#     from utils import (ComicLinkInfo, ComicReader, RqHeaders, SiteReaderLoader,
#                        downld_url, url_join)
# else:
from .utils import (
    ComicLinkInfo,
    ComicReader,
    RqHeaders,
    RqProxy,
    SiteReaderLoader,
    downld_url,
    url_join,
)

logger = logging.getLogger(__name__)


@SiteReaderLoader.register("binb3")
class Binb3(ComicReader):
    def __init__(self, link_info: ComicLinkInfo, driver=None) -> None:
        super().__init__()
        self._link_info = link_info
        self.rq = requests.Session()
        http_adapter = HTTPAdapter(max_retries=5)
        self.rq.mount(prefix="https://", adapter=http_adapter)
        self.rq.mount(prefix="http://", adapter=http_adapter)
        if RqProxy.get_proxy() != None and len(RqProxy.get_proxy()) > 0:
            self.rq.proxies = RqProxy.get_proxy()
        self._headers = {"referer": self._link_info.url}

    def image_coords(self, ptinfo):
        def _str2int(l):
            return [int(x) for x in l]

        pattern = "i:([\d]+),([\d]+)\+([\d]+),([\d]+)>([\d]+),([\d]+)"
        size = []
        for i in range(len(ptinfo)):
            if isinstance(ptinfo[i], (bytes, str)):
                ptinfo[i] = json.loads(ptinfo[i])
            elif ptinfo[i] is None:
                continue

            size.append(
                (ptinfo[i]["views"][0]["width"], ptinfo[i]["views"][0]["height"])
            )
            ptinfo[i] = [
                _str2int(re.match(pattern, s).groups())
                for s in ptinfo[i]["views"][0]["coords"]
            ]
        return ptinfo, size

    def find(
        self, url: str, headers=None, cookies=None, func=lambda x: str(x).zfill(4)
    ) -> tuple:
        NUM_COROUTINES = 5
        MULTI = 100
        r01 = downld_url(
            url=[url_join(url, "data/", func(x) + ".ptimg.json") for x in range(2)],
            headers=headers,
            cookies=cookies,
        )
        start_page = None
        try:
            json.loads(r01[0])
            start_page = 0
        except Exception:
            pass
        try:
            json.loads(r01[1])
            start_page = 1
        except Exception:
            pass
        if start_page is None:
            return None
        s_p = start_page
        end_page = 100
        while True:
            step = (end_page - s_p + 1) / NUM_COROUTINES
            if step <= 1:
                step = 1
            elif int(step) != step:
                step = int(step) + 1
            else:
                step = int(step)
            end_page = s_p + NUM_COROUTINES * step
            tmp = downld_url(
                url=[
                    url_join(url, "data/", func(x) + ".ptimg.json")
                    for x in range(s_p, end_page, step)
                ],
                headers=headers,
                cookies=cookies,
            )
            fail_item_index = []
            for x in range(len(tmp)):
                try:
                    json.loads(tmp[x])
                except Exception:
                    fail_item_index.append(x)
            if len(fail_item_index) == 0:
                if step == 1:
                    return start_page, s_p - 1
                s_p = end_page
                end_page += MULTI
            else:
                if step == 1:
                    return start_page, s_p + (fail_item_index[0] - 1) * step
                s_p = s_p + (fail_item_index[0] - 1) * step
                end_page = s_p + step

    def downloader(self):
        resp = self.rq.get(url=self._link_info.url, headers=RqHeaders())
        # if resp.status_code == 200:
        pg = re.findall('data-ptimg="data/([\d]{4}).ptimg.json"', resp.text)
        ptinfo = [url_join(self._link_info.url, "data/", x + ".ptimg.json") for x in pg]
        ptimgs = [url_join(self._link_info.url, "data/", x + ".jpg") for x in pg]

        if len(pg) > 0:
            ptinfo = downld_url(url=ptinfo, headers=self._headers)
        else:
            # 从页面获取 data-ptimg 信息失败时
            pageinfo = self.find(url=self._link_info.url, headers=self._headers)
            if pageinfo is None:
                logger.warning(
                    "Unable to find resource: {}".format(self._link_info.url)
                )
            inf_url = [
                url_join(self._link_info.url, "data/", str(x).zfill(4) + ".ptimg.json")
                for x in range(pageinfo[0], pageinfo[1] + 1)
            ]
            ptimgs = [
                url_join(self._link_info.url, "data/", str(x).zfill(4) + ".jpg")
                for x in range(pageinfo[0], pageinfo[1] + 1)
            ]
            ptinfo = downld_url(url=inf_url, headers=self._headers)
        ptinfo, size = self.image_coords(ptinfo)
        c_set = 0
        fpath = url_join("./漫畫/", self._link_info.site_name, str((int(time.time()))))
        if cc_mkdir(fpath, model=1) == -1:
            return
        bar = ProgressBar(len(ptinfo))
        while True:
            if c_set >= len(ptinfo):
                break
            end = c_set + 8 if c_set + 8 < len(ptinfo) else len(ptinfo)
            tmp = downld_url(ptimgs[c_set:end], bar=bar)
            for i in range(c_set, end):
                image_ = Image.open(BytesIO(tmp[i - c_set]))
                image_t = Image.new(image_.mode, size=size[i])
                for x in ptinfo[i]:
                    draw_image(image_, image_t, *x)
                image_t.save(url_join(fpath, f"/{i+1}.png"))
            c_set = end


if __name__ == "__main__":
    with open("m.json", "r", encoding="utf-8") as fp:
        ptinfo = json.load(fp)
    from pprint import pprint as print

    lf = ComicLinkInfo("https://comic-meteor.jp/ptdata/nina/0017/")
    reader = Binb3(lf)
    reader.downloader()
