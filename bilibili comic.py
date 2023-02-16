import json
import os
import requests


DOMAIN = "https://manga.bilibili.com"

def transCookie(cookie):
    cookie = cookie.split(';')
    cdict = dict()
    for c in cookie:
        c = c.split('=')
        cdict[c[0]] = c[1]
    return cdict


def downloadImage(token, path):
    file = open(path, 'wb')
    res = requests.get(token, verify=False)
    file.write(res.content)


def getComicDetail(cid):
    url = f"{DOMAIN}/twirp/comic.v1.Comic/ComicDetail?device=pc&platform=web"
    postdata = {'comic_id': cid}
    res = requests.post(url, data=postdata, cookies=cookie, verify=False)
    ret = json.loads(res.text)
    if not os.path.exists('cover.jpg'):
        downloadImage(ret['data']['vertical_cover'], 'cover.jpg')
    eps = ret['data']['ep_list']
    downloadable = dict()
    for ep in eps:
        if not ep["is_locked"] or ep['is_in_free']:
            downloadable[ep['short_title'] + ' ' + ep['title']] = ep['id']
    print(downloadable)
    return downloadable


def getEpImageIndex(epid):
    url = f"{DOMAIN}/twirp/comic.v1.Comic/GetImageIndex?device=pc&platform=web"
    postdata = {'ep_id': epid}
    res = requests.post(url, data=postdata, cookies=cookie, verify=False)
    index = json.loads(res.text)
    return index['data']['images']


def getImageToken(path):
    url = f"{DOMAIN}/twirp/comic.v1.Comic/ImageToken?device=pc&platform=web"
    path += '@1100w.jpg'

    postdict = {"urls": f"[\"{path}\"]"}
    res = requests.post(url, data=postdict, cookies=cookie, verify=False)
    token = json.loads(res.text)['data'][0]
    return token['url'] + "?token=" + token['token']


def auto(cid, cname):
    if not os.path.exists(cname):
        os.makedirs(cname)
    os.chdir(f'.\\{cname}')
    eps = getComicDetail(cid)
    for ep in eps.keys():
        if not os.path.exists(ep):
            os.makedirs(ep)
            os.chdir(f'.\\{ep}')
            index = getEpImageIndex(eps[ep])
            page = 1
            for i in index:
                token = getImageToken(i['path'])
                downloadImage(token, f"{page}.jpg")
                page += 1
            os.chdir('..')


cookie = ''' '''  # 设置cookie值，直接粘贴字符串即可
cookie = transCookie(cookie)
auto(114514, 'example')  # 第一个参数为漫画id，第二个为目录名称
