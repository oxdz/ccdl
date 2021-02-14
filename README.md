# ccdl

This is a package for downloading online comics.

Supported sites:  

+ binb **`*`** :  
  + **`r.binb.jp`**  
  + **`www.cmoa.jp`**  
  + **`booklive.jp`**  
  + **`takeshobo.co.jp`**
  + **`www.comic-valkyrie.com`**  
  + **`futabanet.jp`**  
  + **`comic-polaris.jp`**  
  + **`www.shonengahosha.co.jp`**  
  + **`r-cbs.mangafactory.jp`**  

+ comic_action:  
  + **`comic-action.com`**  
  + **`comic-days.com *`**  
  + **`comic-gardo.com *`**  
  + **`comic-zenon.com`**  
  + **`comicborder.com`**  
  + **`kuragebunch.com`**  
  + **`magcomi.com`**  
  + **`pocket.shonenmagazine.com *`**  
  + **`shonenjumpplus.com *`**  
  + **`tonarinoyj.jp`**  
  + **`viewer.heros-web.com`**  

+ comic_earthstar:  
  + **`viewer.comic-earthstar.jp`**  

+ comic_walker:  
  + **`comic-walker.com`**  

+ ganma:
  + **`ganma.jp`**  

+ urasunday:  
  + **`urasunday.com`**  

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
# or
"""
Reader = SiteReaderLoad.reader_cls(link_info.reader_name)
if Reader:
  reader = Reader(link_info, driver)
else:
  print("not supported")
  return -1
"""

reader.downloader()
```

### Use CcdlSimpleStarter to download comics

> Windows users can download the executable and double-click to run it.  
> The search path for chromedriver is the directory where the application resides.

If chromedriver exists: For sites with \*, if necessary, login in the browser that opens automatically before you enter the URL.You also need to load (you can do this in any TAB) the URL in this browser.  

```sh
$ python CcdlSimpleStarter.py

源碼: https://github.com/vircoys/ccdl

如需登入（含*）請提前在程式啟動的瀏覽器中登入並加載目標url（任意標籤頁）！


>>>>>>>>輸入exit退出<<<<<<<<

url: https://comic-action.com/episode/13933686331709379523
創建文件夾: ./漫畫/ネコ先輩さすがです！/第7話 寝方
|##################################################| 100% (4 of 4)
url:
```  

## LICENSE

[Unlicense License](https://github.com/vircoys/ccdl/blob/master/LICENSE)
