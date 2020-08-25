import base64
import logging
import os
import re
import sys
import time

from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
#from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

img_find_class = ['jvtPwO', 'fqGRlx']


def get_blob(driver, uri):
    """
    通过浏览器中的blob对象获取文件数据
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

# 测试 选择img标签的class


def test_img_class(driver: webdriver.Chrome):

    global img_find_class
    WebDriverWait(driver, 60, 0.4).until(
        lambda x: driver.find_elements_by_class_name("sc-bdVaJa"),
        message="等待頁面init超時（60s）"
    )
 
    WebDriverWait(driver, 60, 0.4).until_not(
        lambda x: driver.find_elements_by_class_name("YSvtd"),
        message="等待頁面影像加載超時（60s）"
    )
    count = 0
    for i in range(len(img_find_class)):
        try:
            WebDriverWait(driver, 12, 0.4).until(
                lambda x: driver.find_elements_by_class_name(
                    img_find_class[i]),
                message="元素定位失敗，找不到圖片"
            )
            break
        except Exception as e:
            logger.warning(e)
            count += 1

    if count >= len(img_find_class):
        raise ValueError("元素定位失敗，找不到圖片")
    else:
        # 将测试成功的class放在列表首
        img_find_class[0], img_find_class[count] = img_find_class[count], img_find_class[0]


def get_page(driver, pages):
    # 图像加载等待，未完全加载时 class 为 YSvtd
    WebDriverWait(driver, 60, 0.4).until_not(
        lambda x: driver.find_elements_by_class_name("YSvtd"),
        message="等待頁面影像加載超時（60s）"
    )

    elems = WebDriverWait(driver, 2, 0.4).until(
        lambda x: driver.find_elements_by_class_name(img_find_class[0]),
        message="元素" + img_find_class[0] + "定位失敗，找不到圖片"
    )

    for x in elems:
        pages[int(re.match("page_([0-9]*)", x.get_attribute("alt")
                           ).group(1))] = x.get_attribute("src")
    return pages


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


def get_image(driver: webdriver.Chrome, url):
    global img_find_class
    try:
        driver.get(url)
        filepath = "ganganonline/" + \
            re.search("chapterId=([0-9]*)", url).group(1)
        creat_dir(filepath)
        test_img_class(driver)
        heartbeat = 5
        page_number = 0
        pages = {}

        pages = get_page(driver, pages)
        # 返回第一页
        while page_number not in pages:
            ActionChains(driver).send_keys(Keys.RIGHT).perform()
        while heartbeat > 0:
            get_page(driver, pages)
            if page_number in pages:
                heartbeat = 5
                with open(filepath + '/{}.jpg'.format(page_number), 'wb') as fp:
                    fp.write(get_blob(driver, pages[page_number]))
                page_number += 1
            else:
                ActionChains(driver).send_keys(Keys.LEFT).perform()
                time.sleep(0.6)
                heartbeat -= 1
        print('下載完成！\n')
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1


if __name__ == "__main__":
    driver = webdriver.Chrome(executable_path="./chromedriver")
    get_image(driver, "https://viewer.ganganonline.com/manga/?chapterId=20950")
