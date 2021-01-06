import base64
import json
import os
import random
import re
import time
from functools import singledispatch, wraps

import requests
from requests import models
from selenium import webdriver

# TODO
# from requests.exceptions import ConnectionError

_site_reader = {
    # "domain": ["reader", RegExp, param1, param2, ...]
    "r.binb.jp":                        ["binb2", "r.binb.jp/epm/([\w-]+)/", 1],
    "www.cmoa.jp":                      ["binb2", "www.cmoa.jp/bib/speedreader/speed.html\?cid=([\w-]+)&u0=(\d)&u1=(\d)", 1],
    "booklive.jp":                      ["binb", "booklive.jp/bviewer/s/\?cid=([\w-]*)&", 1],
    "takeshobo.co.jp":                  ["binb", "[\w-]+.takeshobo.co.jp/manga/([\w-]+)/_files/([0-9]+)/", 0],
    "www.comic-valkyrie.com":           ["binb", "www.comic-valkyrie.com/samplebook/([\w-]*)/", 0],
    "futabanet.jp":                     ["binb", "futabanet.jp/common/dld/zip/([\w-]*)/", 0],
    "comic-polaris.jp":                 ["binb", "comic-polaris.jp/ptdata/([\w-]*)/([\w-]*)/", 0],
    "www.shonengahosha.co.jp":          ["binb", "www.shonengahosha.co.jp/([\w-]*)/([\w-]*)/", 0],

    "comic-action.com":                 ["comic_action", "episode/([\w-]*)", 0],
    "comic-days.com":                   ["comic_action", "episode/([\w-]*)", 1],
    "comic-gardo.com":                  ["comic_action", "episode/([\w-]*)", 1],
    "comic-zenon.com":                  ["comic_action", "episode/([\w-]*)", 0],
    "comicborder.com":                  ["comic_action", "episode/([\w-]*)", 0],
    "kuragebunch.com":                  ["comic_action", "episode/([\w-]*)", 0],
    "magcomi.com":                      ["comic_action", "episode/([\w-]*)", 0],
    "pocket.shonenmagazine.com":        ["comic_action", "episode/([\w-]*)", 1],
    "shonenjumpplus.com":               ["comic_action", "episode/([\w-]*)", 1],
    "tonarinoyj.jp":                    ["comic_action", "episode/([\w-]*)", 0],
    "viewer.heros-web.com":             ["comic_action", "episode/([\w-]*)", 0],

    "viewer.comic-earthstar.jp":        ["comic_earthstar", "cid=([\w-]*)"],

    "comic-walker.com":                 ["comic_walker", 'cid=([\w-]*)'],

    # "viewer.ganganonline.com":          ["ganganonline", None],

    # "www.manga-doa.com":                ["manga_doa", None],

    # "www.sukima.me":                    ["sukima", None],

    # "www.sunday-webry.com":             ["sunday_webry", None],

    "urasunday.com":                    ["urasunday", None],

    "ganma.jp":                         ["ganma", "ganma.jp/(?:([\w-]*)/([\w-]*)|([\w-]*))"]
}


class SiteReaderLoad(object):

    __reader_reg = {}

    @staticmethod
    def readers():
        return [_site_reader[x][0] for x in _site_reader]

    @staticmethod
    def sites():
        return [x for x in _site_reader]

    @staticmethod
    def reader_name(site_name):
        return _site_reader[site_name][0] if site_name in _site_reader else None

    @staticmethod
    def get_param(site_name):
        r"""
        return [RegExp, param1, param2,...]
        """
        return _site_reader[site_name][1:]

    @staticmethod
    def register(reader_name):
        def decorator(reader_cls):
            SiteReaderLoad.__reader_reg[reader_name] = reader_cls
            return reader_cls
        return decorator
    
    @staticmethod
    def reader_cls(reader_name):
        if reader_name in SiteReaderLoad.__reader_reg:
            return SiteReaderLoad.__reader_reg[reader_name]
        else:
            return None


class ComicLinkInfo(object):
    def __init__(self, url):
        super().__init__()
        self._url = url
        self._site_name = None
        self._reader = None
        self._reader_func_entry = None

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        self._url = url

    @property
    def site_name(self):
        match = re.search('//(?:(.*?)/|(.*))', self._url)
        # match = re.search('[a-zA-Z]*//(?:.*\.(.*)|(.*))\..*?/', self._url)
        if not match:
            return None
        match = match.groups()
        match = match[0] if match[0] else match[1]
        if "shonengahosha.co.jp" in match:
            match = "shonengahosha.co.jp"
        return match

    @property
    def reader_name(self):
        return SiteReaderLoad.reader_name(self.site_name)

    @property
    def param(self):
        r"""
        return [param_regexp:list, param1, param2,...]
        """
        param = SiteReaderLoad.get_param(self.site_name)
        if param and type(param) == list and param[0] and type(param[0]) == str:
            search = re.search(param[0], self._url)
            if search:
                param[0] = [x for x in search.groups()]
        return param

    # @property
    # def Reader(self):
    #     return SiteReaderLoad.reader_cls(self.reader_name)


class ProgressBar(object):
    """Progress bar for terminal display

    """

    def __init__(self, total: int):
        """Inits ProgressBar with total"""
        super().__init__()
        self._space = 50
        self._total = total


    def show(self, current_set: int):
        a = int((current_set / self._total) * self._space)
        b = self._space - a
        text = "\r|{}{}| {:>3s}% ({:>} of {:>})".format(
            '#' * a, ' ' * b, str(int((current_set / self._total) * 100)), str(current_set), str(self._total))
        print(text, end='')
        if a == self._space:
            print('')


def draw_image(img_source, img_target, src_x, src_y, swidth, sheight, x, y, width=None, height=None):
    img_target.paste(
        img_source.crop
        (
            (src_x, src_y, src_x + swidth, src_y + sheight),
        ),
        (x, y))


def cc_mkdir(fpath, model=0):
    r"""
    :param model: model = 0, include two subfolders of source and target; model = 1, not include.
    """
    if model == 1:
        if os.path.exists(fpath):
            print('\n當前一話的文件夾{}存在，繼續運行數據將被覆蓋！'.format(fpath))
            print('是否繼續運行？（y/n）')
            yn = input()
            return 0 if yn == 'y' or yn == 'yes' or yn == 'Y' else -1
        else:
            if not os.path.exists(fpath):
                os.makedirs(fpath)
            print('創建文件夾: ' + fpath)
            return 0
    if os.path.exists(fpath+'/source') and os.path.exists(fpath+'/target'):
        print('\n當前一話的文件夾{}存在，繼續運行數據將被覆蓋，'.format(fpath))
        print('是否繼續運行？（y/n）')
        yn = input()
        return 0 if yn == 'y' or yn == 'yes' or yn == 'Y' else -1
    else:
        if not os.path.exists(fpath + '/source'):
            os.makedirs(fpath + '/source')
        if not os.path.exists(fpath + '/target'):
            os.makedirs(fpath + '/target')

        print('創建文件夾: ' + fpath)
        return 0

def get_blob_content(driver:webdriver.Chrome, uri):
    """
    获取浏览器中的blob对象的数据
    """
    result = driver.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)
    if type(result) == int:
        raise Exception("Request failed with status %s" % result)
    return base64.b64decode(result)
    
class RqHeaders(dict):
    def __init__(self):
        super().__init__()
        self.__setitem__(
            'User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36')

    def random_ua(self):
        # self.__setitem__('User-Agent', )
        pass
