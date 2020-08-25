import math
import os
import re
from copy import deepcopy
from io import BytesIO

import execjs
import requests
from PIL import Image
import logging
from .common.progress_bar import progress_bar

logger = logging.getLogger(__name__)


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36"
}


def drawImage(img0, img_copy, src_x, src_y, swidth, sheight, x, y, width=None, height=None):
    img_copy.paste(
        img0.crop
        (
            (src_x, src_y, src_x + swidth, src_y + sheight),
        ),
        (x, y)
    )


js_code = '''
a3E = {
    a3f: function(a, f, b, e, d) {
        var c = Math.floor(a / b),
            g = Math.floor(f / e);
        a %= b;
        f %= e;
        var h, l, k, m, p, r, t, q, v = [];
        h = c - 43 * d % c;
        h = 0 == h % c ? (c - 4) % c : h;
        h = 0 == h ? c - 1 : h;
        l = g - 47 * d % g;
        l = 0 == l % g ? (g - 4) % g : l;
        l = 0 == l ? g - 1 : l;
        0 < a && 0 < f && (k = h * b,
            m = l * e,
            v.push({
                srcX: k,
                srcY: m,
                destX: k,
                destY: m,
                width: a,
                height: f
            }));
        if (0 < f)
            for (t = 0; t < c; t++)
                p = a3E.calcXCoordinateXRest_(t, c, d),
                k = a3E.calcYCoordinateXRest_(p, h, l, g, d),
                p = a3E.calcPositionWithRest_(p, h, a, b),
                r = k * e,
                k = a3E.calcPositionWithRest_(t, h, a, b),
                m = l * e,
                v.push({
                    srcX: k,
                    srcY: m,
                    destX: p,
                    destY: r,
                    width: b,
                    height: f
                });
        if (0 < a)
            for (q = 0; q < g; q++)
                k = a3E.calcYCoordinateYRest_(q, g, d),
                p = a3E.calcXCoordinateYRest_(k, h, l, c, d),
                p *= b,
                r = a3E.calcPositionWithRest_(k, l, f, e),
                k = h * b,
                m = a3E.calcPositionWithRest_(q, l, f, e),
                v.push({
                    srcX: k,
                    srcY: m,
                    destX: p,
                    destY: r,
                    width: a,
                    height: e
                });
        for (t = 0; t < c; t++)
            for (q = 0; q < g; q++)
                p = (t + 29 * d + 31 * q) % c,
                k = (q + 37 * d + 41 * p) % g,
                r = p >= a3E.calcXCoordinateYRest_(k, h, l, c, d) ? a : 0,
                m = k >= a3E.calcYCoordinateXRest_(p, h, l, g, d) ? f : 0,
                p = p * b + r,
                r = k * e + m,
                k = t * b + (t >= h ? a : 0),
                m = q * e + (q >= l ? f : 0),
                v.push({
                    srcX: k,
                    srcY: m,
                    destX: p,
                    destY: r,
                    width: b,
                    height: e
                });
        return v
    },
    calcPositionWithRest_: function(a, f, b, e) {
        return a * e + (a >= f ? b : 0)
    },
    calcXCoordinateXRest_: function(a, f, b) {
        return (a + 61 * b) % f
    },
    calcYCoordinateXRest_: function(a, f, b, e, d) {
        var c = 1 === d % 2;
        (a < f ? c : !c) ? (e = b,
            f = 0) : (e -= b,
            f = b);
        return (a + 53 * d + 59 * b) % e + f
    },
    calcXCoordinateYRest_: function(a, f, b, e, d) {
        var c = 1 == d % 2;
        (a < b ? c : !c) ? (e -= f,
            b = f) : (e = f,
            b = 0);
        return (a + 67 * d + f + 71) % e + b
    },
    calcYCoordinateYRest_: function(a, f, b) {
        return (a + 73 * b) % f
    }
}
'''


def pattern(strs):
    u = 0
    for x in strs+'/0':
        u += ord(x)
    return u % 4 + 1

# def n21():


# proxies = {
#     "http": "http://127.0.0.1：10809",
#     "https": "http://127.0.0.1:10809",
# }


def get_image(driver, url):
    try:
        # https://viewer.comic-earthstar.jp/viewer.html?cid=59e0b2658e9f2e77f8d4d83f8d07ca84&cty=1&lin=0

        cid = re.search("cid=([0-9a-zA-Z]*)", url).group(1)
        run_js = execjs.compile(js_code)

        def setArrayPosi(width, height, num): return run_js.call(
            'a3E.a3f', width, height, 64, 64, num)
        comic_info = requests.get(headers=headers,
                                  url='https://api.comic-earthstar.jp/c.php?cid='+cid).json()
        file_path = 'comic-earthstar/' + \
            re.search(
                'https://storage.comic-earthstar.jp/data/[0-9a-zA-Z]*/([0-9a-zA-Z_-]*)/', comic_info['url']).group(1)
        if os.path.exists(file_path+'/source'):
            print('\n當前一話的文件夾{}存在，繼續運行數據將被覆蓋，'.format(file_path))
            print('是否繼續運行？（y/n）')
            yn = input()
            if yn == 'y' or yn == 'yes' or yn == 'Y':
                print('開始下載...')
            else:
                return -1
        else:
            os.makedirs(file_path+'/source')
            if os.path.exists(file_path+'/target') == False:
                os.makedirs(file_path+'/target')

            print('創建文件夾'+file_path)
            print('開始下載...')
        configuration = requests.get(
            headers=headers, url=comic_info['url'] + 'configuration_pack.json')
        show_bar = progress_bar(len(configuration.json()['configuration']['contents']))
        page_count = 1
        for x in configuration.json()['configuration']['contents']:
            img = requests.get(
                url=comic_info['url']+x['file']+'/0.jpeg').content
            img = Image.open(BytesIO(img))
            img_t = deepcopy(img)
            arrayP = setArrayPosi(img.width, img.height, pattern(x['file']))
            for e in arrayP:
                drawImage(img, img_t, e['destX'], e['destY'], e['width'], e['height'],
                          e['srcX'], e['srcY'])
            img.save(file_path + '/source/' + str(x['index']) + '.jpg')
            img_t.save(file_path + '/target/' + str(x['index']) + '.jpg')
            show_bar.show(page_count)
            page_count += 1
        print("下載完成！\n")
    except Exception as e:
        logger.error(e)
        print(e)
        print("下載失敗!")
        return -1


if __name__ == "__main__":
    get_image(None, 'https://viewer.comic-earthstar.jp/viewer.html?cid=2647c1dba23bc0e0f9cdf75339e120d2&cty=1&lin=0')
