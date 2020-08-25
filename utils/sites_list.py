sites_list = {
    "binb_model_1": {
        "http[s]*://r.binb.jp/epm/([0-9a-zA-Z_]+)/":
            lambda x: "binb/" + x.group(1),
        "http[s]*://www.cmoa.jp/bib/speedreader/speed.html\?cid=([0-9a-zA-Z_]+)":
            lambda x: "cmoa/" + x.group(1),
        'https://booklive.jp/bviewer/s/\?cid=([0-9a-zA-Z_-]*)&':
            lambda x: "booklive/" + x.group(1)
    },
    "binb_model_0": {
        "http[s]*://[0-9a-zA-Z_]+.takeshobo.co.jp/manga/([0-9a-zA-Z_]+)/_files/([0-9]+)/":
            lambda x: "takeshobo/" + x.group(1) + "/" + x.group(2),
        'https://www.comic-valkyrie.com/samplebook/([0-9a-zA-Z_-]*)/':
            lambda x: "comic-valkyrie/" + x.group(1),
        'https://futabanet.jp/common/dld/zip/([0-9a-zA-Z_-]*)/':
            lambda x: "futabanet/" + x.group(1),
        'https://comic-polaris.jp/ptdata/([0-9a-zA-Z_-]*)/([0-9a-zA-Z_-]*)/':
            lambda x: "comic-polaris/" + x.group(1) + "/" + x.group(2),
        "http://www.shonengahosha.co.jp/([0-9a-zA-Z_-]*)/([0-9a-zA-Z_-]*)/":
            lambda x: "shonengahosha/" + x.group(1) + "/" + x.group(2)
    },
    "urasunday": [
        "https://urasunday.com/title/[0-9]*"
    ],
    "comic_walker": [
        'https://comic-walker.com/viewer/'
    ],
    "comic_days": [
        "https://comic-days.com/episode/([0-9a-zA-Z_-]*)"
    ],
    "kuragebunch": [
        "https://kuragebunch.com/episode/([0-9a-zA-Z_-]*)"
    ],
    "shonenmagazine": [
        "https://pocket.shonenmagazine.com/episode/([0-9a-zA-Z_-]*)"
    ],
    "magcomi": [
        "https://magcomi.com/episode/([0-9a-zA-Z_-]*)"
    ],
    "manga_doa": [
        "https://www.manga-doa.com/chapter/([0-9a-zA-Z_-]*)"
    ],
    "sukima": [
        "https://www.sukima.me"
    ],
    "ganganonline": [
        "https://viewer.ganganonline.com/manga/\?chapterId=([0-9a-zA-Z_-]*)"
    ],
    "shonenjumpplus": [
        "https://shonenjumpplus.com/episode/([0-9a-zA-Z]*)"
    ],
    "comic_earthstar": [
        "https://viewer.comic-earthstar.jp/viewer.html\?cid=([0-9a-zA-Z]*)&cty=[0-9]&lin=[0-9]"
    ],
    "comic_action":[
        "https://comic-action.com/episode/([0-9a-zA-Z]*)"
    ],
    "sunday_webry":[
        "https://www.sunday-webry.com/viewer.php\?chapter_id=([0-9a-zA-Z]*)"
    ]
}
