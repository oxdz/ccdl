from __future__ import annotations

import logging
import os
import platform
import sys
import textwrap
import time
import traceback

from selenium import webdriver

from .utils import ComicLinkInfo, RqProxy, SiteReaderLoader, get_windwos_proxy

if not os.path.exists("log"):
    os.makedirs("log")

log_file_path = "log/{}.log".format(time.strftime("%Y-%m-%d"))
fh = logging.FileHandler(filename=log_file_path, encoding="UTF-8")
logging.basicConfig(
    level=logging.INFO,
    handlers=[fh],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("CCDL")

if "Linux" in platform.platform().split("-"):
    executable_path = "./chromedriver"
elif "Windows" in platform.platform().split("-"):
    executable_path = "./chromedriver.exe"
    proxy_server = get_windwos_proxy()
    if proxy_server:
        logger.info(f"Proxy Server Address (Enabled): {proxy_server}")
        RqProxy.set_proxy(proxy_server, proxy_server)
    del proxy_server
else:
    logger.error("platform not win or linux, may failed")
    executable_path = "./chromedriver"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option(
    "excludeSwitches",
    ["enable-automation", "enable-logging"],
)


def main():
    driver = None
    is_exist = os.path.exists(executable_path)
    print(
        textwrap.dedent(
            """
        Source: https://github.com/eggplants/ccdl
        (Forked from: https://github.com/oxdz/ccdl)
        """
        )
    )
    if is_exist:
        print(
            "\nIf you need to login (including *), please login in advance"
            "in the browser where the program is launched and load the target url (any tab)!\n"
        )
        try:
            driver = webdriver.Chrome(
                options=chrome_options,
                executable_path=executable_path,
            )
        except Exception:
            logger.error(traceback.format_exc())
            print(
                textwrap.dedent(
                    f"""
            Chrome failed to start! Please check Chrome and chromedriver version:
            {traceback.format_exc()}

            You can download at:
            http://npm.taobao.org/mirrors/chromedriver/
            OR
            https://chromedriver.chromium.org/downloads
            """
                )
            )

            driver = None
            if input("Do you want to continue? (y/n)") in ("y", "Y", "YES"):
                pass
            else:
                time.sleep(0.8)
                print("Bye~")
                time.sleep(0.8)

                sys.exit()
    else:
        print(
            textwrap.dedent(
                """
        Since chromedriver is not found in the directory where the program is located,
        some of the sites, selenium are needed to download, will not work.

        You can download at:
        http://npm.taobao.org/mirrors/chromedriver/
        OR
        https://chromedriver.chromium.org/downloads
        """
            )
        )

    print("\n>>>>>>>>TYPE `exit` to quit<<<<<<<<\n")

    while True:
        url = input("url: ")

        if url == "exit":
            print("Bye~")
            time.sleep(0.5)
            if driver:
                driver.quit()
            sys.exit()

        try:
            link_info = ComicLinkInfo(url)
        except Exception as e:
            logger.error(f"url: {url}")
            logging.error(e)
            print(f"unsupported url: '{url}'")
            continue
        reader = SiteReaderLoader(link_info, driver)
        if reader is not None:
            try:
                reader.downloader()
            except Exception:
                logger.error(traceback.format_exc())
                print("DOWNLOAD FAILED! \n" + traceback.format_exc())
        else:
            print("not supported")
            continue


if __name__ == "__main__":
    main()
