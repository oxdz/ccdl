import base64
from copy import deepcopy
import json
import logging
import math
import random
import re
from re import L, purge
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL.Image import NONE

import numpy as np
import requests
from lxml.html import etree
from PIL import Image
from requests import cookies
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from .utils import (ComicLinkInfo, ProgressBar, RqHeaders, cc_mkdir,
                    draw_image, get_blob_content)

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
            logger.error(
                "Find element by xpath(\"/html/head/title\"): " + str(e))
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


def getRandomString(t, i=None):
    n = i or "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    r = len(n)
    e = ""
    for x in range(t):
        e += n[math.floor(random.random() * r)]
    return e

def get_cookies_thr_browser(url, driver:webdriver.Chrome):
    r"""
    :param url: comic url
    :param driver: webdriver.Chrome
    :return: dict or None
    """
    for hdl in driver.window_handles:
        driver.switch_to_window(hdl)
        if driver.current_url == url:
            # return driver.get_cookies
            cookies = requests.cookies.RequestsCookieJar()
            for cookie in driver.get_cookies():
                cookies.set(cookie["name"], cookie["value"])
            return cookies
    return None

class DownldGenBinb2(object):
    def __init__(self, manga_info, link_info, base_path, cnt_p, cid, cntserver, ctbl, ptbl, content_data, u0, u1):
        self._manga_info = manga_info
        self._base_path = base_path
        self._link_info = link_info
        self._contents_server = cntserver
        self._cnt_p = cnt_p
        self._cid = cid
        self._ctbl = ctbl
        self._ptbl = ptbl
        self._content_data = content_data
        self._u0 = u0
        self._u1 = u1

    @property
    def file_path_g(self):
        for x in self._manga_info:
            if self._link_info.site_name == "www.cmoa.jp":
                yield self._base_path + "/{}.png".format(int(x["id"][1:]))
            elif self._link_info.site_name == "r.binb.jp":
                yield self._base_path + "/{}.png".format(int(x["id"][1:])+1)
            else:
                raise ValueError("")

    @property
    def img_url_g(self):
        for x in self._manga_info:
            if self._link_info.site_name == "www.cmoa.jp":
                yield self._contents_server + "/sbcGetImg.php?cid={}&src={}&p={}&q=1&vm=1&dmytime={}&u0={}&u1={}".format(
                    self._cid, x["src"].replace("/", "%2F"), self._cnt_p, self._content_data, self._u0, self._u1)
            elif self._link_info.site_name == "r.binb.jp":
                yield "{}{}sbcGetImg.php?cid={}&src={}&p={}&q=1".format(
                    self._link_info._url, self._contents_server, self._cid, x["src"], self._cnt_p
                )
            else:
                raise ValueError("")

    @property
    def coords(self):
        for x in self._manga_info:
            yield ImageDescrambleCoords.ctbl_ptbl(x["src"], self._ctbl, self._ptbl)


class ImageDescrambleCoords(dict):
    def __init__(self, width, height, h, s):
        r"""
        :param width: image width 
        :param height: image height
        :param h: ctbl
        :param s: ptbl
        """
        if "=" == h[0] and "=" == s[0]:
            self.lt_f(h, s)
        e = self.lt_dt({"width": width, "height": height})
        super().__init__({
            "width": e["width"],
            "height": e["height"],
            "transfers": [{
                "index": 0,
                "coords": self.lt_bt({"width": width, "height": height})
            }],
        })

    @staticmethod
    def ctbl_ptbl(t, ctbl_d, ptbl_d):
        r"""
        :param t: t="pages/BouPrlub.jpg"
        :param ctbl_d: ctbl(decoded), list
        :param ptbl_d: ptbl(decoded), list
        """
        i = [0, 0]
        if(t):
            n = t.index('/') + 1
            r = len(t) - n
            for e in range(r):
                i[e % 2] += ord(t[e+n])
            i[0] %= 8
            i[1] %= 8
        h = ctbl_d[i[1]]
        s = ptbl_d[i[0]]
        return h, s

    def lt_f(self, t, i):
        r"""
        :param t: ctbl,str 
        :param i: ptbl,str
        """
        # "^=([0-9]+)-([0-9]+)([-+])([0-9]+)-([-_0-9A-Za-z]+)$/"
        n = re.match(
            "=([0-9]+)-([0-9]+)([-+])([0-9]+)-([-_0-9A-Za-z]+)", t).groups()
        r = re.match(
            "=([0-9]+)-([0-9]+)([-+])([0-9]+)-([-_0-9A-Za-z]+)", i).groups()
        self._lt_T = int(n[0], 10)
        self._lt_j = int(n[1], 10)
        self._lt_xt = int(n[3], 10)
        e = self._lt_T + self._lt_j + self._lt_T * self._lt_j
        if(len(n[4]) == e and len(r[4]) == e):
            s = self.lt_St(n[4])
            h = self.lt_St(r[4])
            self._lt_Ct = s["n"]
            self._lt_At = s["t"]
            self._lt_Tt = h["n"]
            self._lt_Pt = h["t"]
            self._lt_It = []
            for x in range(self._lt_T * self._lt_j):
                self._lt_It.append(s["p"][h["p"][x]])

    def lt_bt(self, t):
        r"""
        :param t: {"width": img width, "height": img height}
        """
        i = t["width"] - 2 * self._lt_T * self._lt_xt
        n = t["height"] - 2 * self._lt_j * self._lt_xt
        r = math.floor((i + self._lt_T - 1) / self._lt_T)
        e = i - (self._lt_T - 1) * r
        s = math.floor((n + self._lt_j - 1) / self._lt_j)
        h = n - (self._lt_j - 1) * s
        u = []
        for o in range(self._lt_T * self._lt_j):
            a = o % self._lt_T
            f = math.floor(o / self._lt_T)
            c = self._lt_xt + a * (r + 2 * self._lt_xt) + \
                (e - r if self._lt_Tt[f] < a else 0)
            l = self._lt_xt + f * (s + 2 * self._lt_xt) + \
                (h - s if self._lt_Pt[a] < f else 0)
            v = self._lt_It[o] % self._lt_T
            d = math.floor(self._lt_It[o] / self._lt_T)
            b = v * r + (e - r if self._lt_Ct[d] < v else 0)
            g = d * s + (h - s if self._lt_At[v] < d else 0)
            p = e if self._lt_Tt[f] == a else r
            m = h if self._lt_Pt[a] == f else s
            0 < i and 0 < n and u.append({
                "xsrc": c,
                "ysrc": l,
                "width": p,
                "height": m,
                "xdest": b,
                "ydest": g
            })
        return u

    def lt_dt(self, t):
        r"""
        :param t: t={width: int, height: int}
        """
        i = 2 * self._lt_T * self._lt_xt
        n = 2 * self._lt_j * self._lt_xt
        if t["width"] >= 64 + i and t["height"] >= 64 + n and t["width"] * t["height"] >= (320 + i) * (320 + n):
            return {
                "width": t["width"] - 2 * self._lt_T * self._lt_xt,
                "height": t["height"] - 2 * self._lt_j * self._lt_xt
            }
        else:
            return t

    def lt_St(self, t):
        kt = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -
              1, -1, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, 63, -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1]
        n = []
        r = []
        e = []
        for x in range(self._lt_T):
            n.append(kt[ord(t[x])])

        for x in range(self._lt_j):
            r.append(kt[ord(t[self._lt_T + x])])

        for x in range(self._lt_T * self._lt_j):
            e.append(kt[ord(t[self._lt_T + self._lt_j + x])])

        # t n p
        return {"t": n, "n": r, "p": e}


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
        count = 8
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
                            lambda x: x.find_element_by_xpath(
                                '//*[@id="content-p{}"]/div/div[{}]/img'.format(i-(1-reader_flag), j)),
                            message="p" + str(i) + "part" + str(j) + "無法定位"
                        )
                    except TimeoutException as e:
                        logger.error(
                            "Find element by id(\"/html/head/title\"): " + str(e))
                        raise e
                    blob_uri = blob_url.get_attribute('src')
                    try:
                        img = Image.open(
                            BytesIO(get_blob_content(self._driver, blob_uri)))
                        img.save(
                            file_path+'/source/{}-{}.png'.format(i, j))
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
                img3t1.paste(imgs[2], (0, imgs[0].size[1] +
                                       imgs[1].size[1] - ij[0] - ij[1]))
                img3t1.save(
                    './{}/target/{}.png'.format(file_path, i))
                start_page += 1
                progress_bar.show(start_page)
            ActionChains(self._driver).send_keys(Keys.LEFT).perform()


class Binb2(object):
    def __init__(self, link_info: ComicLinkInfo, driver:webdriver.Chrome):
        super().__init__()
        self._link_info = link_info
        self._webdriver = driver
        self._url = link_info.url
        self._header = RqHeaders()

    def gen_cntntInfo_url(self, **kwargs):
        if self._link_info.site_name == "www.cmoa.jp":
            return "https://www.cmoa.jp/bib/sws/bibGetCntntInfo.php?cid={}&dmytime={}&k={}&u0={}&u1={}".format(
                self._cid, int(time.time()*1000), self._rq_k, self._u0, self._u1)
        elif self._link_info.site_name == "r.binb.jp":
            return "{}swsapi/bibGetCntntInfo?cid={}&dmytime={}&k={}".format(
                self._link_info.url, self._cid, int(time.time()*1000), self._rq_k)

    def gen_GetCntnt_url(self, **kwargs):
        if self._link_info.site_name == "www.cmoa.jp":
            # print("https://binb-cmoa.sslcs.cdngc.net/sbc/sbcGetCntnt.php?cid={}&p={}&vm=1&dmytime={}&u0=0&u1=0".format(
            #     self._cid, self._cnt_p, self._content_date))
            return "{}/sbcGetCntnt.php?cid={}&p={}&vm=1&dmytime={}&u0={}&u1={}".format(
                self._contents_server, self._cid, self._cnt_p, self._content_date, self._u0, self._u1)
        elif self._link_info.site_name == "r.binb.jp":
            return self._link_info.url + "{}sbcGetCntnt.php?cid={}&p={}&dmytime={}".format(
                self._contents_server, self._cid, self._cnt_p, int(time.time()*1000))

    def gen_image_url(self, img_src, **kwargs):
        if self._link_info.site_name == "www.cmoa.jp":
            return self._contents_server + "/sbcGetImg.php?cid={}&src={}&p={}&q=1&dmytime={}".format(
                self._cid, img_src, self._cnt_p, self._content_date)
        elif self._link_info.site_name == "r.binb.jp":
            return "{}{}sbcGetImg.php?cid={}&src={}&p={}&q=1".format(
                self._url, self._contents_server, self._cid, img_src, self._cnt_p
            )

    def genK(self):
        t = self._cid
        n = getRandomString(16)
        i = t
        r = i[:16]
        e = i[-16:]
        s = 0
        h = 0
        u = 0
        k = []
        for i in range(len(n)):
            s ^= ord(n[i])
            h ^= ord(r[i])
            u ^= ord(e[i])
            k.append(
                n[i] + "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"[s+h+u & 63]
            )
        self._rq_k = "".join(k)
        return self._rq_k

    def CntntInfoDecode(self, t, i, n):
        r"""
        :param t: cid
        :param i: k
        :param n: ctbl ...
        """
        r = t + ":" + i
        e = 0
        for s in range(len(r)):
            e += ord(r[s]) << s % 16
        e &= 2147483647
        if e == 0:
            e = 305419896
        h = ""
        u = e
        for s in range(len(n)):
            if u < 0:
                u = u & 0xffffffff >> 1 ^ 1210056708 & -(1 & u)
            else:
                u = u >> 1 ^ 1210056708 & -(1 & u)
            o = (ord(n[s]) - 32 + u) % 94 + 32
            h += chr(o)
        try:
            return json.loads(h)
        except Exception as e:
            return None

    # step 1
    def get_access(self):
        r"""
        :return: cid, rq.cookies, k
        """
        rq = requests.get(self._link_info.url)
        self._u0 = None
        self._u1 = None
        if rq.status_code != 200:
            e_str = "status_code:{} url:{}".format(
                rq.status_code, self._link_info.url)
            logging.error(e_str)
            raise ValueError(e_str)

        self._cookies = rq.cookies

        if self._link_info.site_name == "r.binb.jp":
            cid = re.search("data-ptbinb-cid=\"(.*?)\"", rq.text).groups()[0]
        elif self._link_info.site_name == "www.cmoa.jp":
            cid = self._link_info.param[0][0]
            self._u0 = self._link_info.param[0][1]
            self._u1 = self._link_info.param[0][2]
            if self._u0 == "0":
                self._cookies = get_cookies_thr_browser(self._url, self._webdriver)

        else:
            logger.error("cid not found, url:{}".format(self._link_info.url))
            raise ValueError("cid not found")
        self._cid = cid

        return cid, self._cookies, self.genK()

    # step 2_1
    def bibGetCntntInfo(self):
        r"""

        """
        rq = requests.get(self.gen_cntntInfo_url(), cookies=self._cookies)
        if rq.status_code != 200:
            return -1
        cntntinfo = rq.json()
        self._manga_title = cntntinfo["items"][0]["Title"]
        if self._manga_title == "":
            self._manga_title = None
        self._manga_subtitle = cntntinfo["items"][0]["SubTitle"]
        if self._manga_subtitle == "":
            self._manga_subtitle = None
        if not (self._manga_subtitle or self._manga_title):
            raise ValueError("")
        self._ptbl = cntntinfo["items"][0]["ptbl"]
        self._ctbl = cntntinfo["items"][0]["ctbl"]
        self._cnt_p = cntntinfo["items"][0]["p"]
        if "ContentDate" in cntntinfo["items"][0]:
            self._content_date = cntntinfo["items"][0]["ContentDate"]
        else:
            self._content_date = None
        self._contents_server = cntntinfo["items"][0]["ContentsServer"]
        self._ptbl = self.CntntInfoDecode(self._cid, self._rq_k, self._ptbl)
        self._ctbl = self.CntntInfoDecode(self._cid, self._rq_k, self._ctbl)

    # step 2_2
    def sbcGetCntnt(self,):
        rq = requests.get(self.gen_GetCntnt_url(), cookies=self._cookies)
        if rq.status_code != 200:
            return -1
        html_mange = rq.json()["ttx"]
        page = etree.HTML(html_mange)
        manga_info_node = page.find(".//t-nocase")
        manga_info_list = list(zip(
            manga_info_node.xpath(".//@id"),
            manga_info_node.xpath(".//@src"),
            manga_info_node.xpath(".//@orgwidth"),
            manga_info_node.xpath(".//@orgheight")))
        self._manga_info = [
            {"id": x[0], "src":x[1], "orgwidth":x[2], "orgheight":x[3]} for x in manga_info_list]
        return self._manga_info

    # step_3
    @staticmethod
    def downld_one(url, fpath, hs, cookies):
        rq = requests.get(url=url, cookies=cookies, headers=RqHeaders())
        if rq.status_code != 200:
            raise ValueError("error:down_one:" + url)
        img = Image.open(BytesIO(rq.content))
        coords = ImageDescrambleCoords(img.width, img.height, hs[0], hs[1])
        img_target = deepcopy(img)
        img_target = Image.new(img.mode, (coords["width"], coords["height"]))
        for y in coords["transfers"][0]["coords"]:
            draw_image(img, img_target, y["xsrc"], y["ysrc"],
                       y["width"], y["height"], y["xdest"], y["ydest"])
        img_target.save(fpath)
        return 0

    def downloader(self):
        self.get_access()
        self.bibGetCntntInfo()
        self.sbcGetCntnt()
        if self._manga_title and self._manga_subtitle:
            base_path = "./漫畫/" + \
                "/".join((self._manga_title, self._manga_subtitle))
        else:
            base_path = "./漫畫/" + self._manga_title if self._manga_title else self._manga_subtitle

        if cc_mkdir(base_path, model=1) != 0:
            return -1
        progressBar = ProgressBar(len(self._manga_info))
        downGen = DownldGenBinb2(self._manga_info, self._link_info, base_path, self._cnt_p,
                                 self._cid, self._contents_server, self._ctbl, self._ptbl, self._content_date, self._u0, self._u1)
        count = 0
        progressBar.show(count)
        with ThreadPoolExecutor(max_workers=4) as executor:
            for x in executor.map(Binb2.downld_one, downGen.img_url_g, downGen.file_path_g, downGen.coords, [self._cookies for x in range(len(self._manga_info))]):
                count += 1
                progressBar.show(count)
