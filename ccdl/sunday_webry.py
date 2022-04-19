import logging
import re

from selenium import webdriver

from .utils import (
    ComicLinkInfo,
    ComicReader,
    ProgressBar,
    SiteReaderLoader,
    cc_mkdir,
    downld_url,
    win_char_replace,
)

logger = logging.getLogger(__name__)

headers = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
    ),
    "accept": "image/webp,image/apng,image/*,*/*;q=0.8",
}


def xor_img(arr_img: list, encryption_hex):
    hex_ = re.findall("(.{1,2})", encryption_hex)
    key_ = []
    for x in hex_:
        key_.append(int(x, 16))
    img_ = []
    len_key_ = len(key_)
    for a in range(len(arr_img)):
        img_.append(arr_img[a] ^ key_[a % len_key_])
    return img_


def write2jpg(file_path, img_, pageNumber):
    with open(file_path + "/" + str(pageNumber) + ".jpg", "wb") as fp:
        for x in img_:
            fp.write((x).to_bytes(length=1, byteorder="big"))


@SiteReaderLoader.register("sunday_webry")
class SundayWebry(ComicReader):
    def __init__(
        self, linkinfo: ComicLinkInfo, driver: webdriver.Chrome = None
    ) -> None:
        super().__init__()
        self._linkinfo = linkinfo
        self._driver = driver

    def downloader(self):
        self._driver.get(self._linkinfo.url)
        pages = self._driver.execute_script("return pages")

        file_path = "./漫畫/" + win_char_replace(
            self._driver.find_element_by_css_selector("div.header-wrapper-label").text
        )

        if cc_mkdir(file_path, 1) != 0:
            return

        total_pages = 0
        for x in pages:
            if "src" in x:
                total_pages += 1
        show_bar = ProgressBar(total_pages)

        url = []
        encryption_hex = []
        page_number = []
        for x in pages:
            if "src" in x:
                url.append(x["src"])
                encryption_hex.append(x["encryption_hex"])
                page_number.append(x["pageNumber"])

        print("Downloading:")
        result = downld_url(url=url, headers=headers, bar=show_bar)
        print("\n")
        print("Decoding:")
        show_bar.reset()
        e_count = 0
        s_count = 0
        for i in range(len(result)):
            if result[i] is not None:
                img = xor_img(result[i], encryption_hex[i])
                write2jpg(file_path, img, page_number[i])
                s_count += 1
                show_bar.show(s_count)
            else:
                e_count += 1
        if e_count != 0:
            print("Failed to get {} of {}".format(e_count, total_pages))
        print("下載完成！\n")


# if __name__ == "__main__":
#     "https://www.sunday-webry.com/viewer.php?chapter_id=27811")
