import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor

import requests

from .utils import ComicLinkInfo, ProgressBar, RqHeaders, cc_mkdir

logger = logging.getLogger(__name__)


# 生成图像解码key
def gen_key_8(url_img_hash: str):
    key_8 = []
    for x in range(0, 16, 2):
        h = url_img_hash[x]+url_img_hash[x+1]
        d = int(h, 16)
        key_8.append(d)
    return key_8


def xor_img(arr_img: list, url_img_hash):
    arr_key = gen_key_8(url_img_hash)
    img_ = []
    for a in range(len(arr_img)):
        img_.append(arr_img[a] ^ arr_key[a % 8])
    return img_


def write2jpg(img_, fpath):
    with open(fpath, 'wb') as fp:
        for x in img_:
            fp.write((x).to_bytes(length=1, byteorder='big'))


class ComicWalker(object):
    def __init__(self, link_info: ComicLinkInfo, driver=None):
        super().__init__()
        self._link_info = link_info
        self._driver = driver

    @staticmethod
    def downld_one(item, fpath):
        url = item['meta']['source_url']
        rr = requests.get(url, headers=RqHeaders())
        if rr.status_code != 200:
            raise ValueError(item['meta']['source_url'])
        write2jpg(xor_img(
            rr.content, item['meta']['drm_hash']), fpath)

    def downloader(self):
        comic_cid = self._link_info.param[0][0]
        rq = requests.get(self._link_info.url, headers=RqHeaders())
        if rq.status_code != 200:
            raise ValueError(self._link_info.url)
        comic_info = json.loads(
            re.search("<script>\sdataLayer[\s\S]*?(\[.*\])[\s\S]*?</script>", rq.text).group(1))[0]
        base_fpath = "./漫畫/" + \
            "/".join([comic_info["content_title"],
                      comic_info["episode_title"]])
        # https://comicwalker-api.nicomanga.jp/api/v1/comicwalker/
        # https://ssl.seiga.nicovideo.jp/api/v1/comicwalker/episodes/
        url_json_comic = 'https://comicwalker-api.nicomanga.jp/api/v1/comicwalker/episodes/' + \
            comic_cid+'/frames'
        r = requests.get(url=url_json_comic, headers=RqHeaders())
        r_json = r.json()
        if cc_mkdir(base_fpath, model=1) != 0:
            return -1
        show_bar = ProgressBar(len(r_json['data']['result']))
        items = [x for x in r_json['data']['result']]
        fpth_l = [base_fpath+"/"+str(x)+".jpg" for x in range(1, len(r_json['data']['result'])+1)]
        with ThreadPoolExecutor(max_workers=4) as executor:
            count = 0
            for x in executor.map(ComicWalker.downld_one, items, fpth_l):
                count += 1
                show_bar.show(count)

# if __name__ == "__main__":
#     'https://comic-walker.com/viewer/?tw=2&dlcl=ja&cid=KDCW_MF00000051010034_68'
