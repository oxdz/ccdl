import json
import logging

import requests
from selenium import webdriver

logger = logging.getLogger(__name__)

from .utils import ComicLinkInfo, RqHeaders


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

        # TODO
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

    def downloader(self):
        pass
        # rq = requests.get(url='', cookies=self._cookies, headers=)
