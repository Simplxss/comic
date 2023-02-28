from lxml import etree
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import os
import re
import time
import json
import requests
from lzstring import LZString

pool = ThreadPoolExecutor(max_workers=4)

DOMAIN = "https://www.manhuagui.com"
DOMAIN2 = "https://i.hamreus.com"

def decode(function, a, c, k):
    # function (p, a, c, k, e, d) {
    #     e = function (c) {
    #         return (c < a ? "" : e(parseInt(c / a))) + ((c = c % a) > 35 ? String.fromCharCode(c + 29) : c.toString(36))
    #     }
    #         ;
    #     if (!''.replace(/^/, String)) {
    #         while (c--)
    #             d[e(c)] = k[c] || e(c);
    #         k = [function (e) {
    #             return d[e]
    #         }
    #         ];
    #         e = function () {
    #             return '\\w+'
    #         }
    #             ;
    #         c = 1;
    #     }
    #     ; while (c--)
    #         if (k[c])
    #             p = p.replace(new RegExp('\\b' + e(c) + '\\b', 'g'), k[c]);
    #     return p;
    # }

    def e(c):
        return ('' if c < a else e(int(c / a))) + [tr(c % a, 36), chr(c % a + 29)][c % a > 35]

    def tr(value, num):
        tmp = itr(value, num)
        return '0' if tmp == '' else tmp

    def itr(value, num):
        d = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return '' if value <= 0 else itr(int(value / num), num) + d[value % num]

    c -= 1
    d = dict()
    while c + 1:
        d[e(c)] = [k[c], e(c)][k[c] == '']
        c -= 1
    pieces = re.split(r'(\b\w+\b)', function)
    js = ''.join([d[x] if x in d else x for x in pieces]).replace('\\\'', '\'')
    return json.loads(re.search(r'^.*\((\{.*\})\).*$', js).group(1))


def downloadImage(page_filename, page_url, params, headers):
    res = requests.get(page_url, params=params, headers=headers)
    file = open(page_filename, 'wb')
    file.write(res.content)


def auto(id, cname):
    if not os.path.exists(cname):
        os.makedirs(cname)
    os.chdir(f'.\\{cname}')

    response = requests.get(f'{DOMAIN}/comic/{id}/')
    html = etree.HTML(response.text)

    chapter_name_list = []
    chapter_url_list = []

    chapter_name_list.extend(html.xpath(
        '//div[@id="chapter-list-1"]/ul/li/a/@title'))
    chapter_url_list.extend(html.xpath(
        '//div[@id="chapter-list-1"]/ul/li/a/@href'))

    task_list = []

    for chapter_name, chapter_url in zip(chapter_name_list, chapter_url_list):
        if os.path.exists(f'.\\{chapter_name}'):
            continue
        os.mkdir(f'.\\{chapter_name}')
        os.chdir(f'.\\{chapter_name}')

        headers = {'Referer': f'{DOMAIN}/comic/{id}/'}

        content = requests.get(f'{DOMAIN}{chapter_url}', headers=headers)

        pattern = re.compile(
            r'^.*\}\(\'(.*)\',(\d*),(\d*),\'([\w|\+|\/|=]*)\'.*$', re.S)

        p, a, c, k = pattern.findall(content.text)[0]
        data = decode(p, int(a), int(c), LZString.decompressFromBase64(k).split('|'))
        path = data['path']

        page = 1
        for filename in data['files']:
            page_filename = f'.\\{filename}'
            task_list.append(pool.submit(
                downloadImage, page_filename, f'{DOMAIN2}{path}{filename}', data['sl'], headers))
            time.sleep(0.1)
            page += 1
        wait(task_list, return_when=ALL_COMPLETED)
        os.chdir('..')


auto(114514, 'example')  # 第一个参数为漫画id，第二个为目录名称
