import json
import random
import re
import time
import os

import requests


_site_reader = {
    # "domain": ["reader", RegEx, param1, param2, ...]
    "r.binb.jp":                        ["binb", None, 1],
    "www.cmoa.jp":                      ["binb", None, 1],
    "booklive.jp":                      ["binb", None, 1],
    "[0-9a-zA-Z_]+.takeshobo.co.jp":    ["binb", None, 0],
    "www.comic-valkyrie.com":           ["binb", None, 0],
    "futabanet.jp":                     ["binb", None, 0],
    "comic-polaris.jp":                 ["binb", None, 0],
    "www.shonengahosha.co.jp":          ["binb", None, 0],

    "comic-action.com":                 ["comic_action", "episode/([0-9a-zA-Z_-]*)", ],
    "kuragebunch.com":                  ["comic_action", "episode/([0-9a-zA-Z_-]*)", ],
    "magcomi.com":                      ["comic_action", "episode/([0-9a-zA-Z_-]*)", ],
    "shonenjumpplus.com":               ["comic_action", "episode/([0-9a-zA-Z_-]*)", ],
    "pocket.shonenmagazine.com":        ["comic_action", "episode/([0-9a-zA-Z_-]*)", ],
    "comic-days.com":                   ["comic_action", "episode/([0-9a-zA-Z_-]*)", ],

    "viewer.comic-earthstar.jp":        ["comic_earthstar", None],

    "comic-walker.com":                 ["comic_walker", None],

    "viewer.ganganonline.com":          ["ganganonline", None],

    "www.manga-doa.com":                ["manga_doa", None],

    "www.sukima.me":                    ["sukima", None],

    "www.sunday-webry.com":             ["sunday_webry", None],

    "urasunday.com":                    ["urasunday", None]
}


class SiteReaderLoad(object):
    @staticmethod
    def readers():
        return [_site_reader[x][0] for x in _site_reader]

    @staticmethod
    def sites():
        return [x for x in _site_reader]

    @staticmethod
    def get_reader(site_name):
        return _site_reader[site_name][0] if site_name in _site_reader else None

    @staticmethod
    def get_param(site_name):
        return _site_reader[site_name][1:]

    # @staticmethod
    # def get_reader_func_entry(reader):
    #     return globals()[reader].get_image if reader in globals() else None


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
        return match[0] if match[0] else match[1]

    @property
    def reader(self):
        return SiteReaderLoad.get_reader(self.site_name)

    @property
    def param(self):
        param = SiteReaderLoad.get_param(self.site_name)
        if param and type(param) == list and param[0] and type(param[0]) == str:
            search = re.search(param[0], self._url)
            if search:
                param[0] = [x for x in search.groups()]
        return param

    # @property
    # def func_entry(self):
    #     return SiteReaderLoad.get_reader_func_entry(self.reader)


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


def draw_image(img0, img_copy, src_x, src_y, swidth, sheight, x, y, width=None, height=None):
    img_copy.paste(
        img0.crop
        (
            (src_x, src_y, src_x + swidth, src_y + sheight),
        ),
        (x, y))


def cc_mkdir(fpath):
    if os.path.exists(fpath+'/source') and os.path.exists(fpath+'/target'):
        print('\n當前一話的文件夾{}存在，繼續運行數據將被覆蓋，'.format(fpath))
        print('是否繼續運行？（y/n）')
        yn = input()
        if yn == 'y' or yn == 'yes' or yn == 'Y':
            return 0
        else:
            return -1
    else:
        if not os.path.exists(fpath + '/source'):
            os.makedirs(fpath + '/source')
        if not os.path.exists(fpath + '/target'):
            os.makedirs(fpath + '/target')

        print('創建文件夾' + fpath)
        return 0

class RqHeaders(dict):
    def __init__(self):
        super().__init__()
        self.__setitem__(
            'User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36')

    def random_ua(self):
        # self.__setitem__('User-Agent', )
        pass
