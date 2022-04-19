import logging
import re
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from io import BytesIO

import execjs  # type: ignore[import]
import requests
from PIL import Image

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

logger = logging.getLogger(__name__)


js_code = """
a3E = {
    a3f: function(a, f, b, e, d) {
        var c = Math.floor(a / b),
            g = Math.floor(f / e);
        a %= b;
        f %= e;
        var h, l, k, m, p, r, t, q, v = [];
        h = c - 43 * d % c;
        h = 0 == h % c ? (c - 4) % c : h;
        h = 0 == h ? c - 1 : h;
        l = g - 47 * d % g;
        l = 0 == l % g ? (g - 4) % g : l;
        l = 0 == l ? g - 1 : l;
        0 < a && 0 < f && (k = h * b,
            m = l * e,
            v.push({
                srcX: k,
                srcY: m,
                destX: k,
                destY: m,
                width: a,
                height: f
            }));
        if (0 < f)
            for (t = 0; t < c; t++)
                p = a3E.calcXCoordinateXRest_(t, c, d),
                k = a3E.calcYCoordinateXRest_(p, h, l, g, d),
                p = a3E.calcPositionWithRest_(p, h, a, b),
                r = k * e,
                k = a3E.calcPositionWithRest_(t, h, a, b),
                m = l * e,
                v.push({
                    srcX: k,
                    srcY: m,
                    destX: p,
                    destY: r,
                    width: b,
                    height: f
                });
        if (0 < a)
            for (q = 0; q < g; q++)
                k = a3E.calcYCoordinateYRest_(q, g, d),
                p = a3E.calcXCoordinateYRest_(k, h, l, c, d),
                p *= b,
                r = a3E.calcPositionWithRest_(k, l, f, e),
                k = h * b,
                m = a3E.calcPositionWithRest_(q, l, f, e),
                v.push({
                    srcX: k,
                    srcY: m,
                    destX: p,
                    destY: r,
                    width: a,
                    height: e
                });
        for (t = 0; t < c; t++)
            for (q = 0; q < g; q++)
                p = (t + 29 * d + 31 * q) % c,
                k = (q + 37 * d + 41 * p) % g,
                r = p >= a3E.calcXCoordinateYRest_(k, h, l, c, d) ? a : 0,
                m = k >= a3E.calcYCoordinateXRest_(p, h, l, g, d) ? f : 0,
                p = p * b + r,
                r = k * e + m,
                k = t * b + (t >= h ? a : 0),
                m = q * e + (q >= l ? f : 0),
                v.push({
                    srcX: k,
                    srcY: m,
                    destX: p,
                    destY: r,
                    width: b,
                    height: e
                });
        return v
    },
    calcPositionWithRest_: function(a, f, b, e) {
        return a * e + (a >= f ? b : 0)
    },
    calcXCoordinateXRest_: function(a, f, b) {
        return (a + 61 * b) % f
    },
    calcYCoordinateXRest_: function(a, f, b, e, d) {
        var c = 1 === d % 2;
        (a < f ? c : !c) ? (e = b,
            f = 0) : (e -= b,
            f = b);
        return (a + 53 * d + 59 * b) % e + f
    },
    calcXCoordinateYRest_: function(a, f, b, e, d) {
        var c = 1 == d % 2;
        (a < b ? c : !c) ? (e -= f,
            b = f) : (e = f,
            b = 0);
        return (a + 67 * d + f + 71) % e + b
    },
    calcYCoordinateYRest_: function(a, f, b) {
        return (a + 73 * b) % f
    }
}
"""

run_js = execjs.compile(js_code)


def setArrayPosi(width, height, num):
    return run_js.call("a3E.a3f", width, height, 64, 64, num)


def pattern(strs):
    u = 0
    for x in strs + "/0":
        u += ord(x)
    return u % 4 + 1


class DownldGen(object):
    def __init__(self, contents, base_fpath, base_url):
        super().__init__()
        self._contents = contents
        self._base_fpath = base_fpath
        self._base_url = base_url

    @property
    def file_path_g(self):
        for x in self._contents:
            yield [
                self._base_fpath,
                re.search(r"item/xhtml/([\w-]+).xhtml", x["file"]).group(1) + ".png",
            ]

    @property
    def img_url_g(self):
        for x in self._contents:
            yield [self._base_url, x["file"], "/0.jpeg"]


@SiteReaderLoader.register("comic_earthstar")
class ComicEarthstar(ComicReader):
    def __init__(self, link_info: ComicLinkInfo, driver=None):
        super().__init__()
        self._link_info = link_info
        self._driver = driver

    @staticmethod
    def downld_one(url: list, fpath: list):
        rq = requests.get("".join(url), proxies=RqProxy.get_proxy())
        if rq.status_code != 200:
            raise ValueError("".join(url))
        img = Image.open(BytesIO(rq.content))
        img_t = deepcopy(img)
        arrayP = setArrayPosi(img.width, img.height, pattern(url[1]))
        for e in arrayP:
            draw_image(
                img,
                img_t,
                e["destX"],
                e["destY"],
                e["width"],
                e["height"],
                e["srcX"],
                e["srcY"],
            )
        img.save(fpath[0] + "/source/" + fpath[1])
        img_t.save(fpath[0] + "/target/" + fpath[1])

    def downloader(self):
        cid = self._link_info.param[0][0]

        comic_info = requests.get(
            headers=RqHeaders(),
            url="https://api.comic-earthstar.jp/c.php?cid=" + cid,
            proxies=RqProxy.get_proxy(),
        ).json()
        base_file_path = (
            "./漫畫/"
            + re.search(
                "https://storage.comic-earthstar.jp/data/([0-9a-zA-Z]*)/[0-9a-zA-Z_-]*/",
                comic_info["url"],
            ).group(1)
            + "/"
            + comic_info["cti"]
        )
        if cc_mkdir(base_file_path) != 0:
            return -1
        configuration = requests.get(
            headers=RqHeaders(), url=comic_info["url"] + "configuration_pack.json"
        )
        show_bar = ProgressBar(len(configuration.json()["configuration"]["contents"]))
        downldGen = DownldGen(
            configuration.json()["configuration"]["contents"],
            base_file_path,
            comic_info["url"],
        )
        with ThreadPoolExecutor(max_workers=4) as executor:
            count = 0
            for x in executor.map(
                self.downld_one, downldGen.img_url_g, downldGen.file_path_g
            ):
                count += 1
                show_bar.show(count)
        # https://viewer.comic-earthstar.jp/viewer.html?cid=59e0b2658e9f2e77f8d4d83f8d07ca84&cty=1&lin=0
