# ccdl - online **C**omi**C** **D**own**L**oader

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/eggplants/ccdl/master.svg)](https://results.pre-commit.ci/latest/github/eggplants/ccdl/master)

*[Original project](https://github.com/oxdz/ccdl)
*ccdl is available under Unlicense License*

This is a package for downloading online comics.

Supported Viewers and Sites:

- [BinB] (by [VOYAGER]):
  - `r.binb.jp`
  - `www.cmoa.jp`
  - `booklive.jp`
  - `takeshobo.co.jp`
  - `www.comic-valkyrie.com`
  - `futabanet.jp`
  - `comic-polaris.jp`
  - `www.shonengahosha.co.jp`
  - `r-cbs.mangafactory.jp`
  - `comic-meteor.jp`

[BinB]: https://www.voyager.co.jp/products/binb/
[VOYAGER]: https://www.voyager.co.jp/

- [Giga Viewer] (by [Hatena]):
  - `comic-action.com`
  - `comic-days.com`
  - `comic-gardo.com`
  - `comic-zenon.com`
  - `comic-trail.com`
  - `comicborder.com`
  - `comicbushi-web.com`
  - `kuragebunch.com`
  - `ichijin-plus.com`
  - `magcomi.com`
  - `pocket.shonenmagazine.com`
  - `shonenjumpplus.com`
  - `sunday-webry.com`
  - `tonarinoyj.jp`
  - `to-corona-ex.com`
  - `viewer.heros-web.com`
  - `sunday-webry.com`

[Giga Viewer]: https://hatenacorp.jp/press/release/search?q=GigaViewer
[Hatena]: https://www.hatena.ne.jp/

- Comic Earth Star Viewer (by [EARTH STAR Entertainment]):
  - `viewer.comic-earthstar.jp`

[EARTH STAR Entertainment]: https://www.earthstar.jp/

- ComicWalker Viewer (by [KADOKAWA]):
  - `comic-walker.com`

[KADOKAWA]: https://group.kadokawa.co.jp/

- [PUBLUS Reader] (by [ACCESS]):
  - `www.ganganonline.com`

[PUBLUS Reader]: https://publus.jp/
[ACCESS]: https://www.access-company.com/

- Ganma! Viewer (by [COMICSMART]):
  - `ganma.jp`

[COMICSMART]: https://www.comicsmart.co.jp/

- ZAO Viewer (Unconfirmed, by Unknown):
  - `urasunday.com`
  - (`mangaplus.shueisha.co.jp`)

- [Magazine Viewer] (by [COMICI]):
  - `yanmaga.jp`

[Magazine Viewer]: https://prtimes.jp/main/html/rd/p/000000016.000041778.html
[COMICI]: https://comici.jp/

## Install

For some sites, you'll need a version of [chromedriver](http://npm.taobao.org/mirrors/chromedriver/) that matches the version of Chrome you've installed.

```shellsession
$ pip install git+https://github.com/oxdz/ccdl

# Download the chromedriver
$ wget https://cdn.npm.taobao.org/dist/chromedriver/86.0.4240.22/chromedriver_linux64.zip
$ unzip chromedriver_linux64.zip
$ rm chromedriver_linux64.zip
```

## Usage

### Strat with the code, for example

```python
from selenium import webdriver

from ccdl import ComicLinkInfo
from ccdl import Binb2, ComicAction, Ganma


url = "https://comic-action.com/episode/13933686331709379523"

driver = webdriver.Chrome(executable_path='./chromedriver')

link_info = ComicLinkInfo(url)

reader = ComicAction(link_info, driver)
# or
"""
reader = SiteReaderLoader(link_info, driver)
reader.downloader() if reader else print("不支持的網站")
"""

reader.downloader()
```

### Use CcdlSimpleStarter to download comics

Windows users can download the executable and double-click to run it.
The search path for chromedriver is the directory where the application resides.

If chromedriver exists:
For sites with \*, if necessary, login in the browser that opens automatically before you enter the URL.
You also need to load (you can do this in any TAB) the URL in this browser.

```shellsession
$ ccdl

源碼: https://github.com/oxdz/ccdl

如需登入（含*）請提前在程式啟動的瀏覽器中登入並加載目標url（任意標籤頁）！


>>>>>>>>輸入exit退出<<<<<<<<

url: https://comic-action.com/episode/13933686331709379523
創建文件夾: ./漫畫/ネコ先輩さすがです！/第7話 寝方
|##################################################| 100% (4 of 4)
url:
```

## Build executable

If you want to build the smallest executable file, please use the virtual environment to build

```shellsession
# create venv
$ python -m venv ./venv

# active venv
$ ./venv/Scripts/activate

# install
$ ./venv/Scripts/pip install .[dev]

# build executable
# If there is an error that the file top_level.txt does not exist, create a new one
$ ./venv/Scripts/pyinstaller -F ./src/ccdl/main.py
```

## LICENSE

[Unlicense License](https://github.com/oxdz/ccdl/blob/master/LICENSE)
