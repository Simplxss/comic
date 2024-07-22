# from asyncio import sleep
import os
import re
import time
import base64
from lxml import etree
from collections import deque
from curl_cffi import requests
from Crypto.Cipher import AES, ARC4
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


def decrypt_aes_ecb(data, key):
    key = bytes(key, encoding="utf-8")
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(data), AES.block_size)


def decrypt_aes_cbc(data, key):
    cipher = AES.new(key, AES.MODE_CBC, iv=b"0000000000000000")
    return unpad(cipher.decrypt(data), AES.block_size)


def decrypt_arc4(raw, key):
    raw = bytes(raw.decode(), encoding="utf-16-le")
    data = bytearray(len(raw) // 2)
    for i in range(0, len(raw), 2):
        data[i // 2] = raw[i]

    key = bytes(key, encoding="utf-8")
    cipher = ARC4.new(key)

    return cipher.decrypt(data)


def decode_const(data):
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
    with open(page_filename, "wb") as file:
        file.write(decrypt_aes_cbc(res.content, key))


manga_read_js = visit(f"{DOMAIN}/js/manga.read.js")
aK = deque(
    [
        i[1:-1]
        for i in re.findall(r"var aK=\[(.*?)\];", manga_read_js.text)[0].split(",")
    ]
)
offset = re.findall(r"f=f-(0x[0-f]*);", manga_read_js.text)[0]
condition, value = re.findall(r"var f=(.*?);.*?\(c,(0x[0-f]*)\)", manga_read_js.text)[0]

table = re.findall(
    r"G==ag\((0x[0-9a-f]*?)\)&&\(I=ag\((0x[0-9a-f]*?)\)\),", manga_read_js.text
)

offset = int(offset, 16)
condition = re.sub(
    r"parseInt\(N\((0x[0-f]*)\)\)", lambda N: f"parseInt(N({N.group(1)}))", condition
)

value = int(value, 16)

manga_read_js_decode_const = lambda N: decode_const(aK[N - offset])

N = lambda N: manga_read_js_decode_const(N).decode()
parseInt = lambda i: int(re.search(r"^\d+", i).group())

while True:
    try:
        if eval(condition) == value:
            break
        else:
            aK.rotate(-1)
    except:
        aK.rotate(-1)

KEY_TABLE = {
    manga_read_js_decode_const(int(k, 16)).decode(): manga_read_js_decode_const(
        int(v, 16)
    )
    for k, v in table
}

custom_js = visit(f"{DOMAIN}/js/custom.js")
c = deque(
    [
        i[1:-1]
        for i in re.findall(
            r"function c\(\){var [a-zA-Z][0-9a-zA-Z]=\[(.*?)\];c=function\(\){return [a-zA-Z][0-9a-zA-Z];};return c\(\);}",
            custom_js.text,
        )[0].split(",")
    ]
)
offset = re.findall(r"f=f-(0x[0-f]*?);", custom_js.text)[0]
condition, value = re.findall(r"var g=(.*?);.*?\(c,(0x[0-f]*?)\)", custom_js.text)[0]

offset = int(offset, 16)
condition = re.sub(
    r"parseInt\([a-z]{2}\((0x[0-f]*?)\)\)",
    lambda N: f"parseInt(d({N.group(1)}))",
    condition,
)
condition = re.sub(
    r"parseInt\([a-z]{2}\((0x[0-f]*?),\'(.{4})\'\)\)",
    lambda N: f'parseInt(e({N.group(1)}, "{N.group(2)}"))',
    condition,
)

value = int(value, 16)

custom_js_decode_const = lambda m: decode_const(c[m - offset])

d = lambda a: custom_js_decode_const(a).decode(errors="ignore")
e = lambda a, b: decrypt_arc4(custom_js_decode_const(a), b).decode(errors="ignore")

while True:
    try:
        if eval(condition) == value:
            break
        else:
            c.rotate(-1)
    except:
        c.rotate(-1)

v1, v2 = re.findall(r"^var (.{2}=.),(.{2}=.);", custom_js.text)[0]
exec(f"{v1}\n{v2}")

v1, v2, v3, v4 = re.findall(
    r"function\(\){var (.{2}=.{1,2}),(.{2}=.{1,2}),(f=\{.*?\});(.*?)\}\(\)",
    custom_js.text,
)[0]
exec(f"{v1}\n{v2}")
exec(re.sub(r"function\(.*?\)\{return .*?;\}", "''", v3))

val = re.findall(r"var (.{2}=.{2}),(.{2}=.{2})", v4)
for v1, v2 in val:
    exec(f"{v1}\n{v2}")

a1, a2, a3, a4, a5, a6 = re.findall(
    r"var h=(f\[.*\]),i;.*?i=window\[.{5,25}\]\[.{5,25}\]\((f\[.{5,25}\]),window\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\(window\[.{5,25}\]\)\[.{5,25}\]\(window\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\)\);.*?var .=__cad\[.{5,25}\]\(\),.=mh_info\[.{5,25}\],.=f\[.{5,25}\]\(.\[0x0\],.\[.{5,25}\]\(\)\),.=f\[.{5,25}\]\(.\[0x1\],.\[.{5,25}\]\(\)\),.=(f\[.{5,25}\]),.;.*?.=window\[.{5,25}\]\[.{5,25}\]\((f\[.{5,25}\]),window\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\(window\[.{5,25}\]\[.{5,25}\]\)\[.{5,25}\]\(window\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\)\).*?;.=(f\[.{5,25}\]);.*?.=window\[.{5,25}\]\[.{5,25}\]\((f\[.{5,25}\]),window\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\(window\[.{5,25}\]\[.{5,25}\]\)\[.{5,25}\]\(window\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\[.{5,25}\]\)\)",
    v4,
)[0]
C_DATA_KEY1 = eval(a1)
C_DATA_KEY2 = eval(a2)
ENC_CODE1_KEY1 = eval(a5)
ENC_CODE1_KEY2 = eval(a6)
ENC_CODE2_KEY1 = eval(a3)
ENC_CODE2_KEY2 = eval(a4)

v1, v2, v3, v4 = re.findall(
    r"\}\};\(function\(\){var (.{2}=.{1,2}),(.{2}=.{1,2}),(a=\{.*?\});(.*?)\}\);\}\(\)",
    custom_js.text,
)[0]
exec(f"{v1}\n{v2}")
exec(re.sub(r"function\(.*?\)\{return .*?;\}", "''", v3))

val = re.findall(r"var (.{2}=.{2}),(.{2}=.{2})", v4)
for v1, v2 in val:
    exec(f"{v1}\n{v2}")

a1, a2 = re.findall(r"var .=(a\[.{2,15}\]);.*f=(a\[.{2,15}\]);", v4)[0]
IMG_KEY_KEY1 = eval(a1)
IMG_KEY_KEY2 = eval(a2)

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
            mh_info = decrypt_aes_ecb(C_DATA, C_DATA_KEY1).decode()
        except:
            mh_info = decrypt_aes_ecb(C_DATA, C_DATA_KEY2).decode()

        pattern = re.compile(
            r'startimg:([0-9]*),.*?enc_code1:"(.*?)",.*?enc_code2:"(.*?)",.*?keyType:"(.*?)",.*?imgKey:"(.*?)"',
            re.S,
        )

        startimg, enc_code1, enc_code2, keyType, imgKey = pattern.findall(mh_info)[0]

        enc_code2 = base64.b64decode(base64.b64decode(enc_code2).decode())
        try:
            _tka_ = decrypt_aes_ecb(
                enc_code2,
                ENC_CODE2_KEY1,
            ).decode()  # _tka_ + mh_info["pageid"]
        except:
            _tka_ = decrypt_aes_ecb(
                enc_code2,
                ENC_CODE2_KEY2,
            ).decode(
                "gbk"
            )  # _tka_ + mh_info["pageid"]

        enc_code1 = base64.b64decode(base64.b64decode(enc_code1).decode())
        try:
            _tkb_ = decrypt_aes_ecb(
                enc_code1,
                ENC_CODE1_KEY1,
            ).decode()  # _tkb_ + mh_info["pageid"]
        except:
            _tkb_ = decrypt_aes_ecb(
                enc_code1,
                ENC_CODE1_KEY2,
            ).decode()  # _tkb_ + mh_info["pageid"]

        if imgKey != "":
            imgKey = base64.b64decode(imgKey)
            try:
                imgKey = decrypt_aes_ecb(
                    imgKey,
                    IMG_KEY_KEY1,
                )
            except:
                imgKey = decrypt_aes_ecb(
                    imgKey,
                    IMG_KEY_KEY2,
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


auto("ll4514", "example")  # 第一个参数为漫画id，第二个为目录名称
