import json
import logging
from concurrent.futures import ThreadPoolExecutor
from operator import add
from os import write
from time import sleep, time

import requests
from requests.api import get
from selenium import webdriver

from .utils import ComicLinkInfo, ProgressBar, RqHeaders, cc_mkdir

logger = logging.getLogger(__name__)


class DownldGen(object):
    def __init__(self, item):
        self._item = item

    @property
    def file_path_g(self):
        base_path = "./漫畫/" + \
            "/".join((self._item["series"]["title"], self._item["title"]))
        for x in self._item["page"]["files"]:
            yield base_path + "/" + x

    @property
    def img_url_g(self):
        base_url = self._item["page"]["baseUrl"]
        token = self._item["page"]["token"]
        for x in self._item["page"]["files"]:
            yield base_url + x + token


class GanmaRqHeaders(RqHeaders):
    def __init__(self, manga_alias=None):
        super().__init__()
        self._manga_alias = manga_alias

    def aslogin(self):
        self.__setitem__("x-from", "https://ganma.jp/_cd/login")
        return self

    def aslogout(self):
        self.__setitem__(
            "x-from",
            "https://ganma.jp/announcement",
        )
        return self

    def asmangainfo(self):
        self.__setitem__("x-from", "https://ganma.jp/" + self._manga_alias)
        return self


class Ganma(object):
    def __init__(self, link_info: ComicLinkInfo, driver=None):
        super().__init__()
        self._link_info = link_info
        self._param = self._link_info.param[0]
        if self._param[2]:
            self._param[0], self._param[2] = self._param[2], self._param[0]
        elif not self._param[0] and not self._param[2]:
            raise ValueError(
                "Unable to get comic alias from URL! URL:{}".format(
                    self._link_info.url))
        self._manga_alias = self._param[0]
        self._cookies = None
        self._headers = GanmaRqHeaders(self._manga_alias)

    def manga_info(self):
        rq = requests.get(url='https://ganma.jp/api/2.0/magazines/' +
                          self._manga_alias,
                          headers=self._headers.asmangainfo(),
                          cookies=self._cookies)
        if rq.status_code != 200:
            logger.warning(str(rq.status_code) + ' ' + rq.text)
            return -1
        try:
            resp = rq.json()
        except ValueError as e:
            logger.error(
                "The response body does not contain valid json!\nstatus:{}, text:{}"
                .format(rq.status_code, rq.text))
            raise e
        mangainfo = {}
        if 'success' in resp and resp['success']:
            mangainfo['items'] = resp['root']['items']
            mangainfo['index_id'] = [x['id'] for x in mangainfo['items']]
            mangainfo['index_title'] = [
                x['title'] for x in mangainfo['items']
            ]

        return mangainfo

    def login(self, mail, passwd):
        if type(mail) != str or type(passwd) != str:
            logger.error("帳號（email）或密碼非法 type：{}，{}".format(
                type(mail), type(passwd))),
            raise ValueError("帳號（email）或密碼非法 type：{}，{}".format(
                type(mail), type(passwd)))
        rq = requests.post(url='https://ganma.jp/api/1.0/session?mode=mail',
                           json={
                               "password": passwd,
                               "mail": mail
                           },
                           headers=self._headers)

        try:
            resp = rq.json()
        except ValueError as e:
            logger.error(
                "The response body does not contain valid json!\nstatus:{}, text:{}"
                .format(rq.status_code, rq.text))
            raise e

        if 'success' in resp:
            if resp['success']:
                if 'PLAY_SESSION' in rq.cookies:
                    self._cookies = {
                        'PLAY_SESSION': rq.cookies['PLAY_SESSION']
                    }
                    return 0
            else:
                raise ValueError("帳號（email）或密碼錯誤")
        else:
            logger.error("The key 'success' does not exist! text:{}".format(
                rq.text))
            raise ValueError("The key 'success' does not exist!")

    def logout(self):
        rq = requests.delete(url="https://ganma.jp/api/1.0/session",
                             headers=self._headers.aslogout(),
                             cookies=self._cookies)
        self._cookies = None
        if rq.status_code == 200:
            return 0
        else:
            return -1

    @staticmethod
    def downld_one(url, fpath):
        rq = requests.get(url=url, headers=RqHeaders())
        if rq.status_code != 200:
            raise ValueError(url)
        else:
            with open(fpath, "wb") as fp:
                fp.write(rq.content)
        return 0

    def downloader(self):
        manga_info = self.manga_info()

        if self._param[1] and self._param[1] in manga_info["index_id"]:
            indx = manga_info["index_id"].index(self._param[1])
        else:
            raise ValueError("当前一话不存在或需要登录".format())

        dir = "./漫畫/" + \
            manga_info["items"][indx]["series"]["title"] + \
            "/" + manga_info["items"][indx]["title"]
        cc_mkdir(dir, model=1)

        progress_bar = ProgressBar(
            len(manga_info["items"][indx]["page"]["files"]))

        downld_gen = DownldGen(manga_info["items"][indx])

        with ThreadPoolExecutor(max_workers=8) as executor:
            count = 0
            for x in executor.map(Ganma.downld_one, downld_gen.img_url_g,
                                  downld_gen.file_path_g):
                count += 1
                progress_bar.show(count)

        if manga_info["items"][indx]["afterwordImage"]["url"]:
            print("下載後記圖片！", end=" ")
            rq = requests.get(
                url=manga_info["items"][indx]["afterwordImage"]["url"], headers=RqHeaders())
            if rq.status_code != 200:
                logger.error("Error, afterword image: " +
                             manga_info["items"][indx]["afterwordImage"]["url"])
                raise ValueError(manga_info["items"]
                                 [indx]["afterwordImage"]["url"])
            with open(dir + "/afterword.jpg", "wb") as fp:
                fp.write(rq.content)
            print("成功！")
        else:
            print("No afterword image found!")
