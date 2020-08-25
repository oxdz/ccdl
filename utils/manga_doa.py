import base64
import copy
import json
import logging
import os
import re
import time
from io import BytesIO

import requests
from PIL import Image
from .common.progress_bar import progress_bar

logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"
}


def creat_dir(file_path):
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
        return 0


def genKey(b64str):
    """
    生成图像解码的key
    """
    key = []
    str = base64.b64decode(b64str)
    for i in str:
        key.append(i)
    return key


def write2file_jpg(fp, target_img):
    """
    将图像写入磁盘
    """
    for x in target_img:
        fp.write((x).to_bytes(length=1, byteorder='big'))



def image_decode(img_list, key: list):
    """
    图像解码
    """
    img_ = []
    len_key = len(key)
    for a in range(len(img_list)):
        img_.append(img_list[a] ^ key[a % len_key])
    return img_



# driver unused
def get_image(driver, url: str):
    try:
        file_path = "manga_doa/" + \
            re.search('chapter/([0-9a-zA-Z_-]*)', url).group(1) +'/'
        # 创建文件夹
        if creat_dir(file_path) == -1:
            return -1

        response = requests.get(url, headers=headers)

        # 获得图像信息json对象
        img_json = json.loads(
            re.search("var chapters = (.*)", response.text).group(1)[:-1]
        )

        img_list = []

        total_pages = 0
        for x in img_json:
            x = x["images"][0]
            if "key" in x:
                total_pages += 1
        show_bar = progress_bar(total_pages)
        c_page = 1
        for x in img_json:
            x = x["images"][0]
            if "key" not in x:
                continue
            key = genKey(x["key"])
            # 下载未解码的图像数据
            content = requests.get(x["path"], headers=headers).content
            with open(file_path + str(c_page) + '.jpg', 'wb') as fp:
                write2file_jpg(fp, image_decode(content, key))
            show_bar.show(c_page)
            c_page += 1

        print('下載完成！\n')
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1


if __name__ == "__main__":
    get_image(None, "https://www.manga-doa.com/chapter/56046")
