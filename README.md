# ccdl

This is a package for downloading online comics.

> The old version has been moved to branch m.v1.6 !

Supported sites:  

+ binb:  
  + **`r.binb.jp`**  
  + **`www.cmoa.jp`**  
  + ~~`booklive.jp`~~
  + ~~`www.comic-valkyrie.com`~~
  + ~~`futabanet.jp`~~
  + ~~`comic-polaris.jp`~~
  + ~~`www.shonengahosha.co.jp`~~  

+ comic_action:
  + **`comic-action.com`**
  + **`comic-days.com`**
  + **`comic-gardo.com`**
  + **`comic-zenon.com`**
  + **`comicborder.com`**
  + **`kuragebunch.com`**
  + **`magcomi.com`**
  + **`pocket.shonenmagazine.com`**
  + **`shonenjumpplus.com`**
  + **`tonarinoyj.jp`**
  + **`viewer.heros-web.com`**

+ ganma:
  + **`ganma.jp`**

## Install

For some sites, you'll need a version of [chromedriver](http://npm.taobao.org/mirrors/chromedriver/) that matches the version of Chrome you've installed.

```sh
  $ git clone git@github.com:vircoys/ccdl.git

  $ cd ./ccdl
  
  # install dependencies
  $ pip install -r requirements.txt
  
  # install ccdl
  $ python ./setup.py install --user
  
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
reader.downloader()
```

### Use CcdlSimpleStarter to download comics

> Windows users can download the executable and double-click to run it.  
> The search path for chromedriver is the directory where the application resides.

If chromedriver exists: For sites with \* before the serial number, if necessary, login in the browser that opens automatically before you enter the URL. If it is \*\*, you also need to load (you can do this in any TAB) the URL in this browser.  

```sh
$ python CcdlSimpleStarter.py

源碼: https://github.com/vircoys/ccdl

（序號含*）如需登入請提前在程式啟動的瀏覽器中登入，(**)並加載目標url（任意標籤頁）！

Supported sites:

   *1. r.binb.jp/epm/([\w_]+)/
  **2. www.cmoa.jp/bib/speedreader/speed.html\?cid=([\w-]+)&u0=(\d)&u1=(\d)

    3. ganma.jp/xx/xx-xx-xx-xx.../...

    4. comic-action.com/episode/([\w-]*)
   *5. comic-days.com/episode/([\w-]*)
   *6. comic-gardo.com/episode/([\w-]*)
    7. comic-zenon.com/episode/([\w-]*)
    8. comicborder.com/episode/([\w-]*)
    9. kuragebunch.com/episode/([\w-]*)
   10. magcomi.com/episode/([\w-]*)
   11. pocket.shonenmagazine.com/episode/([\w-]*)
  *12. shonenjumpplus.com/episode/([\w-]*)
  *13. tonarinoyj.jp/episode/([\w-]*)
   14. viewer.heros-web.com/episode/([\w-]*)


>>>>>>>>輸入exit退出<<<<<<<<

url: https://comic-action.com/episode/13933686331709379523
創建文件夾: ./漫畫/ネコ先輩さすがです！/第7話 寝方
|##################################################| 100% (4 of 4)
url:
```  

## LICENSE

[Unlicense License](https://github.com/vircoys/ccdl/blob/master/LICENSE)
