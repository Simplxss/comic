from lxml import etree
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import os
import re
import time
import requests
from lzstring import LZString

pool = ThreadPoolExecutor(max_workers=32)


def downloadImage(page_filename, page_url):
    res = requests.get(page_url, headers={
                       'Referer': 'https://www.maofly.com/'})
    file = open(page_filename, 'wb')
    file.write(res.content)


def auto(id, cname):
    if not os.path.exists(cname):
        os.makedirs(cname)
    os.chdir(f'.\\{cname}')

    response = requests.get(
        f'https://www.maofly.com/manga/{id}.html')
    myhtml = etree.HTML(response.content.decode())

    chapter_url_list = myhtml.xpath("//a[@class='fixed-a-es']/@href")
    chapter_name_list = myhtml.xpath("//a[@class='fixed-a-es']/@title")

    task_list = []

    # 遍历所有章节
    for chapter_name, chapter_url in zip(chapter_name_list, chapter_url_list):
        if os.path.exists(f'.\\{chapter_name}'):
            continue
        os.mkdir(f'.\\{chapter_name}')
        os.chdir(f'.\\{chapter_name}')

        print(chapter_name)

        response = requests.get(chapter_url)
        img_data = re.findall(r'img_data = "(.*?)"', response.text)[0]
        page_url_list = LZString.decompressFromBase64(img_data).split(',')
        
        page = 1
        for page_url in page_url_list:
            page_filename = f'.\\{page}.jpg'
            downloadImage(
                page_filename, f'http://mao.mhtupian.com/uploads/{page_url}')
            time.sleep(0.1)
            # task_list.append(pool.submit(
            #    downloadImage, page_filename, f'https://mao.mhtupian.com/uploads/{page_url}'))
            page += 1
        os.chdir('..')

    wait(task_list, return_when=ALL_COMPLETED)


auto(114514, 'example')  # 第一个参数为漫画id，第二个为目录名称
