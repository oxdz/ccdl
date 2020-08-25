import requests
import re
import os
import logging

from .common.progress_bar import progress_bar
logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"
}


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


def write2jpg(img_path, img_, num: int):
    with open(img_path+'/'+str(num)+'.jpg', 'wb') as fp:
        for x in img_:
            fp.write((x).to_bytes(length=1, byteorder='big'))


# driver unused
def get_image(driver, url: str):
    try:
        comic_cid = re.search('cid=([0-9a-zA-Z_-]*)', url).group(1)
        file_path = "comic_walker/" + comic_cid
        url_json_comic = 'https://ssl.seiga.nicovideo.jp/api/v1/comicwalker/episodes/' + \
            comic_cid+'/frames'
        if os.path.exists(file_path):
            print('\n當前一話的文件夾{}存在，繼續運行數據將被覆蓋，'.format(file_path))
            print('是否繼續運行？（y/n）')
            yn = input()
            if yn == 'y' or yn == 'yes' or yn == 'Y':
                print('開始下載...')
            else:
                return -1
        else:
            os.makedirs(file_path)
            print('創建文件夾'+file_path)
            print('開始下載...')
        r = requests.get(url=url_json_comic, headers=headers)
        r_json = r.json()
        a = 1
        show_bar = progress_bar(len(r_json['data']['result']))
        for x in r_json['data']['result']:
            rr = requests.get(x['meta']['source_url'], headers=headers)
            if x['meta']['drm_hash'] != None:
                write2jpg(file_path, xor_img(
                    rr.content, x['meta']['drm_hash']), a)
            else:
                with open(file_path+'/'+str(a)+'.jpg', 'wb') as fp:
                    fp.write(rr.content)
            show_bar.show(a)
            a += 1
        print('下載完成！\n')
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1


if __name__ == "__main__":
    get_image(
        None, 'https://comic-walker.com/viewer/?tw=2&dlcl=ja&cid=KDCW_MF00000051010034_68')
