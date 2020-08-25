import base64
import logging
import os
import re
import time
import numpy as np

from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from .common.progress_bar import progress_bar

logger = logging.getLogger(__name__)

# 页面元素加载的最大等待时间
WAIT_TIME = 90


#  输入什么都会继续运行，懒得改了，bug涉及模块较多
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


# def similar_pixel_count(ar):      # 统计相同色块
#     c = 0
#     for y in ar:
#         if y[0] and y[1] and y[2]:
#             c += 1
#     return c


def edge_connection_offset(img_np):
    ij = []
    for x in range(len(img_np)-1):
        cnt = []
        h = img_np[x].shape[0]
        for y in range(10):
            cnt.append(
                sum(abs(img_np[x][h-1] - img_np[x+1][y]))
            )
        ij.append(cnt.index(max(cnt))+1)
    return ij


def page_number(driver: webdriver.Chrome):
    """
    return [current_page_numb:int, total_numb:int]
    """
    page_elem_id = 'menu_slidercaption'
    try:
        pageNum = \
            WebDriverWait(
                driver, WAIT_TIME, 0.5
            ).until(
                lambda x: x.find_element_by_id(page_elem_id),
                message="無法定位元素 " + page_elem_id + ", 獲取頁碼資訊失敗"
            ).get_attribute('innerText').split('/')
    except Exception as e:
        logger.error(e)
        raise e
    pageNum[1] = int(pageNum[1])
    if(pageNum[0] != '-'):
        pageNum[0] = int(pageNum[0])
    else:
        pageNum[0] = pageNum[1]
    return pageNum


def get_file_content(driver, uri):
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


# site_model == 0: p1~
# binb
# cmoa

# site_model == 1: p0 ~
# futabanet
# takeshobo
# comic-valkyrie
# https://comic-polaris.jp/ptdata/sukiani/0017/
def get_image(driver: webdriver.Chrome, url, file_path, site_model: int):
    try:
        creat_dir(file_path+"/tmp")
        driver.get(url)
        time.sleep(2)
        # 返回到第一页, 这段代码基本不会执行
        head_flag = 0
        while(page_number(driver)[0] != 1):
            if (page_number(driver)[0] == 2):
                head_flag += 1
                if (head_flag >= 3):
                    break
            ActionChains(driver).send_keys(Keys.RIGHT).perform()
        pre_page = 0
        c_page = page_number(driver)[0]
        t_page = page_number(driver)[1]
        if os.path.exists(file_path+'/c_page.txt'):
            with open(file_path+'/c_page.txt', 'r', encoding='utf-8') as fp:
                try:
                    c_page = int(fp.read())
                    pre_page = c_page-1
                except Exception as e:
                    logger.warning('中斷処頁碼解析失敗，將重新下載...')
                    print('中斷頁碼解析失敗，將重新下載...')
            while(page_number(driver)[0] < c_page):
                ActionChains(driver).send_keys(Keys.LEFT).perform()
        show_bar = progress_bar(t_page)
        page_count = 1
        while(c_page <= t_page):
            time.sleep(1.5)
            if c_page == t_page - 1:
                c_page = t_page
            for i in range(c_page - 1 + site_model, pre_page - 1 + site_model, -1):
                img_c3 = []
                # ! 需要测试每张图是否分成三部分
                for j in range(1, 3+1):
                    try:
                        img_blob = \
                            WebDriverWait(
                                driver, WAIT_TIME, 0.5
                            ).until(
                                lambda x: x.find_element_by_xpath(
                                    '//*[@id="content-p{}"]/div/div[{}]/img'.format(
                                        i, j)
                                ),
                                message="p" + str(i) + "part" + str(j) + "無法定位"
                            ).get_attribute('src')
                    except Exception as e:
                        with open(file_path + '/c_page.txt', 'w', encoding='utf-8') as fp:
                            fp.write(str(i)+'\n')
                        raise Exception("網頁圖片加載异常，請檢查網絡！當前頁碼保存: c_page.txt")

                    content_data = get_file_content(driver, img_blob)
                    image_1of3 = Image.open(BytesIO(content_data))
                    image_1of3.save('{}/tmp/{}-{}.jpeg'.format(file_path, i, j))
                    img_c3.append(image_1of3)
                img_np = []
                for x in img_c3:
                    img_np.append(np.array(x.convert('1')).astype(int))
                    ij = edge_connection_offset(img_np)
                w = 0
                h = 0
                for x in img_c3:
                    w += x.size[0]
                    h += x.size[1]
                w = int(w/3)
                img3t1 = Image.new('RGB', (w, h-12))
                img3t1.paste(img_c3[0], (0, 0))
                img3t1.paste(img_c3[1], (0, img_c3[0].size[1]-ij[0]))
                img3t1.paste(
                    img_c3[2],
                    (0, img_c3[0].size[1] + img_c3[1].size[1] - ij[0] - ij[1])
                )
                img3t1.save('{}/{}.jpeg'.format(file_path, i))
                show_bar.show(page_count)
                page_count += 1
            if c_page == t_page:
                print('下載完成！\n')
                break
            pre_page = c_page
            ActionChains(driver).send_keys(Keys.LEFT).perform()
            c_page = page_number(driver)[0]
    except Exception as e:
        logger.error(e)
        print("下載失敗!")
        return -1
