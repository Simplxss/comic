# from asyncio import sleep
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import os
import time
import requests

from lxml import etree

import urllib3
urllib3.disable_warnings()

DOMAIN = 'https://www.colamanhua.com'

s = requests.session()
s.headers['sec-ch-ua'] = '''"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"'''
s.headers['sec-ch-ua-mobile'] = '''?0'''
s.headers['sec-ch-ua-platform'] = '''"Windows"'''
s.headers['Upgrade-Insecure-Requests'] = '''1'''
s.headers['User-Agent'] = '''Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'''
s.headers['Accept'] = '''text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'''
s.headers['Sec-Fetch-Site'] = '''none'''
s.headers['Sec-Fetch-Mode'] = '''navigate'''
s.headers['Sec-Fetch-User'] = '''?1'''
s.headers['Sec-Fetch-Dest'] = '''document'''
s.headers['Accept-Language'] = '''zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7'''
s.headers['Accept-Encoding'] = '''gzip, deflate'''


pool = ThreadPoolExecutor(max_workers=4)


def E_trans_to_C(string):
    E_pun = u'*,!?'
    C_pun = u'x，！？'
    table = {ord(f): ord(t) for f, t in zip(E_pun, C_pun)}
    return string.translate(table)


def downloadImage(page_filename, page_url):
    r = requests.session()
    r.headers['sec-ch-ua'] = '''"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"'''
    r.headers['sec-ch-ua-mobile'] = '''?0'''
    r.headers['sec-ch-ua-platform'] = '''"Windows"'''
    r.headers['Upgrade-Insecure-Requests'] = '''1'''
    r.headers['User-Agent'] = '''Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'''
    r.headers['Accept'] = '''text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'''
    r.headers['Sec-Fetch-Site'] = '''none'''
    r.headers['Sec-Fetch-Mode'] = '''navigate'''
    r.headers['Sec-Fetch-User'] = '''?1'''  
    r.headers['Sec-Fetch-Dest'] = '''document'''
    r.headers['Accept-Language'] = '''zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7'''
    r.headers['Accept-Encoding'] = '''gzip, deflate'''
    r.verify = False   # verify去除ssl认证
    res = r.get(page_url)
    file = open(page_filename, 'wb')
    file.write(res.content)


def auto(id, cname):
    if not os.path.exists(cname):
        os.makedirs(cname)
    os.chdir(f'.\\{cname}')

    response = s.get(f'{DOMAIN}/{id}')

    myhtml = etree.HTML(response.text)
    chapter_url_list = myhtml.xpath(
        "//div[@class='all_data_list']/ul/li/a/@href")
    chapter_name_list = myhtml.xpath(
        "//div[@class='all_data_list']/ul/li/a/@title")

    task_list = []

    # 遍历所有章节
    for chapter_name, chapter_url in zip(chapter_name_list, chapter_url_list):
        chapter_name = E_trans_to_C(chapter_name)
        if os.path.exists(f'.\\{chapter_name}'):
            continue
        os.mkdir(f'.\\{chapter_name}')
        os.chdir(f'.\\{chapter_name}')

        print(chapter_name)

        response = s.get(f'{DOMAIN}{chapter_url}')

        myhtml = etree.HTML(response.text)

        page_url_list = myhtml.xpath(
            "//div[@class='acgn-reader-chapter__swiper-box']/a/img/@data-echo")
        page = 1
        for page_url in page_url_list:
            page_filename = f'.\\{page}.jpg'
            # downloadImage(page_filename, page_url)
            task_list.append(pool.submit(
                downloadImage, page_filename, page_url))
            time.sleep(0.1)
            page += 1
        wait(task_list, return_when=ALL_COMPLETED)
        os.chdir('..')


# s.proxies = {'http': '', 'https': ''} # 代理

auto(114514, 'example')  # 第一个参数为漫画id，第二个为目录名称
