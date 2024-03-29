# from asyncio import sleep
import os
import re
import time
import base64
from lxml import etree
from collections import deque
from curl_cffi import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

DOMAIN = "https://www.colamanga.com"
DOMAIN_IMG = "https://img.colamanga.com"


def visit(url):
    return requests.get(url, impersonate="chrome110")


def download(url, Referer):
    return requests.get(
        url, headers={"Origin": DOMAIN, "Referer": Referer}, impersonate="chrome110"
    )


def decrypt_ecb(data, key):
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(data), AES.block_size)


def decrypt_cbc(data, key):
    cipher = AES.new(key, AES.MODE_CBC, iv=b"0000000000000000")
    return unpad(cipher.decrypt(data), AES.block_size)


def decode_str(N):
    data = aK[N - 0x1F0]
    missing_padding = 4 - len(data) % 4
    if missing_padding != 4:
        data += "=" * missing_padding
    DEFAULT = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    CUSTOM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return base64.b64decode(data.translate(str.maketrans(CUSTOM, DEFAULT)))


def E_trans_to_C(string):
    E_pun = "*,!?"
    C_pun = "x，！？"
    table = {ord(f): ord(t) for f, t in zip(E_pun, C_pun)}
    return string.translate(table)


def downloadImage(page_filename, page_url, Referer, key):
    res = download(page_url, Referer)
    file = open(page_filename, "wb")
    file.write(decrypt_cbc(res.content, key))


cal = lambda N: int(re.match(r"^\d+", decode_str(N).decode()).group())

js = visit(f"{DOMAIN}/js/manga.read.js")
aK = deque([i[1:-1] for i in re.findall(r"var aK=\[(.*?)\];", js.text)[0].split(",")])
table = re.findall(r"G==ag\((0x[0-9a-f]*?)\)&&\(I=ag\((0x[0-9a-f]*?)\)\),", js.text)
condition, value = re.findall(r"var f=(.*?);.*?\(c,(0x[0-f]*)\)", js.text)[0]

condition = re.sub(
    r"parseInt\(N\((0x[0-f]*)\)\)", lambda N: f"cal({N.group(1)})", condition
)
value = int(value, 0)

while True:
    try:
        if eval(condition) == value:
            break
        else:
            aK.rotate(-1)
    except:
        aK.rotate(-1)

KEY_TABLE = {decode_str(int(k, 0)).decode(): decode_str(int(v, 0)) for k, v in table}

pool = ThreadPoolExecutor(max_workers=4)


def auto(id, cname):
    if not os.path.exists(cname):
        os.makedirs(cname)
    os.chdir(f".\\{cname}")

    response = visit(f"{DOMAIN}/manga-{id}")

    myhtml = etree.HTML(response.text)
    chapter_url_list = myhtml.xpath("//div[@class='all_data_list']/ul/li/a/@href")
    chapter_name_list = myhtml.xpath("//div[@class='all_data_list']/ul/li/a/@title")

    task_list = []

    # 遍历所有章节
    for chapter_name, chapter_url in zip(chapter_name_list, chapter_url_list):
        chapter_name = E_trans_to_C(chapter_name)
        chapter_url = f"{DOMAIN}{chapter_url}"
        if os.path.exists(f".\\{chapter_name}"):
            continue
        os.mkdir(f".\\{chapter_name}")
        os.chdir(f".\\{chapter_name}")

        print(chapter_name)

        response = visit(chapter_url)

        C_DATA = re.findall(r"var C_DATA=\'(.*?)\';", response.text)[0]

        C_DATA = base64.b64decode(base64.b64decode(C_DATA).decode())
        try:
            mh_info = decrypt_ecb(C_DATA, b"NhDvbPWFVjc326Qs").decode()
        except:
            mh_info = decrypt_ecb(C_DATA, b"P3XtlTunjedzg5lw").decode()

        pattern = re.compile(
            r'startimg:([0-9]*),.*?enc_code1:"(.*?)",.*?enc_code2:"(.*?)",.*?keyType:"(.*?)",.*?imgKey:"(.*?)"',
            re.S,
        )

        startimg, enc_code1, enc_code2, keyType, imgKey = pattern.findall(mh_info)[0]

        enc_code2 = base64.b64decode(base64.b64decode(enc_code2).decode())
        try:
            _tka_ = decrypt_ecb(
                enc_code2,
                b"q50Fah4uhqkyChdP",
            ).decode()  # _tka_ + mh_info["pageid"]
        except:
            _tka_ = decrypt_ecb(
                enc_code2,
                b"0aW5swj3TBKSrfBU",
            ).decode(
                "gbk"
            )  # _tka_ + mh_info["pageid"]

        enc_code1 = base64.b64decode(base64.b64decode(enc_code1).decode())
        try:
            _tkb_ = decrypt_ecb(
                enc_code1,
                b"n3MGPalwQZBOvr6t",
            ).decode()  # _tkb_ + mh_info["pageid"]
        except:
            _tkb_ = decrypt_ecb(
                enc_code1,
                b"7bxIyR0nLydU9vlQ",
            ).decode()  # _tkb_ + mh_info["pageid"]

        if imgKey != "":
            imgKey = base64.b64decode(imgKey)
            try:
                imgKey = decrypt_ecb(
                    imgKey,
                    b"P3XtlTunjedzg5lw",
                )
            except:
                imgKey = decrypt_ecb(
                    imgKey,
                    b"NhDvbPWFVjc326Qs",
                )

        for page in range(int(startimg), int(_tkb_) + 1):
            if keyType != "0" and keyType != "":
                task_list.append(
                    pool.submit(
                        downloadImage,
                        f".\\{page}.webp",
                        f"{DOMAIN_IMG}/comic/{_tka_}{page:0>4d}.enc.webp",
                        chapter_url,
                        KEY_TABLE[keyType],
                    )
                )
            elif imgKey != "":
                task_list.append(
                    pool.submit(
                        downloadImage,
                        f".\\{page}.webp",
                        f"{DOMAIN_IMG}/comic/{_tka_}{page:0>4d}.enc.webp",
                        chapter_url,
                        imgKey,
                    )
                )
            else:
                task_list.append(
                    pool.submit(
                        downloadImage,
                        f".\\{page}.jpg",
                        f"{DOMAIN_IMG}/comic/{_tka_}{page:0>4d}.jpg",
                        chapter_url,
                    )
                )
            time.sleep(0.1)
        wait(task_list, return_when=ALL_COMPLETED)
        os.chdir("..")
    os.chdir("..")


auto(114514, 'example')  # 第一个参数为漫画id，第二个为目录名称
