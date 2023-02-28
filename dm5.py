import time
import os
import re
import execjs
import requests

from lxml import etree
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

pool = ThreadPoolExecutor(max_workers=4)

DOMAIN = "https://www.dm5.com"


def downloadImage(headers, page_filename, page_url):
    res = requests.get(page_url, headers=headers)
    file = open(page_filename, 'wb')
    file.write(res.content)


def auto(id, cname):
    if not os.path.exists(cname):
        os.makedirs(cname)
    os.chdir(f'.\\{cname}')

    response = requests.get(f'{DOMAIN}/{id}/')
    html = etree.HTML(response.text)

    chapter_name_list=[]
    chapter_url_list = []

    chapter_name_list.extend(html.xpath(
        '//div[@id="chapterlistload"]/ul/li/a/text()[1]'))
    chapter_url_list.extend(html.xpath(
        '//div[@id="chapterlistload"]/ul/li/a/@href'))

    chapter_name_list.extend(html.xpath(
        '//ul[@class="chapteritem"]/li/a/text()[1]'))
    chapter_url_list.extend(html.xpath(
        '//ul[@class="chapteritem"]/li/a/@href'))

    task_list = []

    for chapter_name, chapter_url in zip(chapter_name_list, chapter_url_list):
        if os.path.exists(f'.\\{chapter_name}'):
            continue
        os.mkdir(f'.\\{chapter_name}')
        os.chdir(f'.\\{chapter_name}')

        headers = {'Referer': f'{DOMAIN}/{id}/'}

        content = requests.get(f'{DOMAIN}{chapter_url}', headers=headers)

        pattern = re.compile(
            '.*?DM5_MID=(.*?);'
            '.*?DM5_CID=(.*?);'
            '.*?DM5_IMAGE_COUNT=(.*?);'
            '.*?DM5_VIEWSIGN="(.*?)";'
            '.*?DM5_VIEWSIGN_DT="(.*?)";', re.S)

        mid, cid, image_count, sign, date = pattern.findall(content.text)[0]

        for i in range(1, int(image_count)):
            content = requests.get(
                f'{DOMAIN}/{id}/chapterfun.ashx?cid={cid}&page={i}&key=&language=1&gtk=6&_cid={cid}&_mid={mid}&_dt={date}&_sign={sign}', headers=headers)

            js = "function run(){{return {0:s}}}".format(content.text[5:-2])
            ctx = execjs.compile(js).call('run')
            ctx = execjs.compile(ctx).call('dm5imagefun')

            page_filename = f'.\\{i}.jpg'
            task_list.append(pool.submit(
                downloadImage,headers, page_filename, ctx[0]))
            time.sleep(0.1)
        wait(task_list, return_when=ALL_COMPLETED)
        os.chdir('..')


auto('manhua-example', 'example')
