import json
import logging

import requests
from selenium import webdriver

logger = logging.getLogger()

# from .utils import ComicLinkInfo, RqHeaders

class Ganma(object):
    def __init__(self, mail=None, passwd=None):
        super().__init__()
        self._cookies = None
        if mail !=None and passwd !=None and type(mail) == str and type(passwd) == str:
            try:    
                self._cookies = ganma.login(mail, passwd)
            except ValueError as e:
                print(e)
    
    @staticmethod
    def login(mail, passwd):
        if type(mail) != str or type(passwd) != str:
            logger.error("帳號（email）或密碼 type：{}，{}", type(mail), type(passwd))
            raise ValueError("帳號（email）或密碼 type：{}，{}", type(mail), type(passwd))

        _headers = {
            # "User-Agent": RqHeaders.random_ua(),
            "accept": "application/json, text/plain, */*",
            "accept-language":
            "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7,en-US;q=0.6,en-GB;q=0.5",
            "content-type": "application/json;charset=UTF-8",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-from": "https://ganma.jp/_cd/login",
        }

        rq = requests.post(
            url='https://ganma.jp/api/1.0/session?mode=mail',
            json={
                "password": passwd,
                "mail": mail
            },
            headers=_headers)

        try:
            resp = rq.json()
        except ValueError as e:
            logger.error(
                "The response body does not contain valid json!\nstatus:{}, text:{}"
                .format(rq.status_code, resp.text))
            raise e

        if 'success' in resp:
            if resp['success']:
                if 'PLAY_SESSION' in rq.cookies:
                    return {'PLAY_SESSION': rq.cookies['PLAY_SESSION']}
            else:
                raise ValueError("帳號（email）或密碼錯誤")
        else:
            logger.error("The key 'success' does not exist! text:{}".format(
                rq.text))
            raise ValueError("The key 'success' does not exist!")

    @staticmethod
    def logout(cookies):
        _headers = {
            # "User-Agent": RqHeaders.random_ua(),
            "accept": "application/json, text/plain, */*",
            "accept-language":
            "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7,en-US;q=0.6,en-GB;q=0.5",
            "content-type": "application/json;charset=UTF-8",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-from": "https://ganma.jp/announcement",
        }
        rq = requests.delete(url="https://ganma.jp/api/1.0/session",
                            headers=_headers,
                            cookies=cookies)
        if rq.status_code == 200:
            return 0
        else:
            return -1


    def downloader(self, link_info, driver: webdriver.Chrome):
        pass
        


if __name__ == "__main__":
    cookies = {}
    aa = ganma.login('vircoys@gmail.com', 'Alpha00X')
    print(ganma.logout(aa))
    b = 2
    print("ee")
