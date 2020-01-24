import re
import requests
from itertools import combinations as cmb
from bs4 import BeautifulSoup as bs

sess = requests.Session()

def to_dict(string):
    string = string.strip()
    l = string.split('\n')
    ret_dict = {}
    for line in l:
        line = line.split(': ')
        if ':' not in line[0]:
            ret_dict[line[0]] = line[1]
    return ret_dict


def get_html(url):
    """
    Args:
        url(str): target dcard article url
    Return:
        html(str): html text
    """
    res = sess.get(url)
    if res.status_code == 200:
        return res.text
    else:
        raise Exception(f'URL {url} unreachable.')
def get_links(soup):
    """
    Args:
        soup(bs): BeautifulSoup object
    Return:
        links(list): ppt.cc links, str
    """
    links = soup.find_all('a', href=re.complie('.*ppt\.cc.*'))
    links = list(map(lambda a: a.text, links))
    return links


def search_reply(soup):
    reply_author = soup.select(".PostAuthor_root_3vAJfe")
    passwd_set = set()
    for author in reply_author:
        if '原PO' in author.text:
            tmp = author.find_parent('div', class_='CommentEntry_entry_3SaSrr').find(
                'div', class_='CommentEntry_content_1ATrw1').select('div > div > div')
            # print(tmp)
            for i in tmp:
                if 'https' not in i.text:
                    passwd_set.add(i.text.strip())
                    # print(i.text)
    return passwd_set


"""
- [v] Original Poster's replies(only rows)
- [ ] Date
"""
def get_password(soup):
    passwd_set = search_reply(soup)
    for passwd in passwd_set:
        print(passwd)


def download(media_type, url, passwd_set):
    sess_ = requests.Session()

    if media_type == 'img':
        website_url = url
        resource_url = url + '@.jpg'
        # header = {
        #     'cookie': 'PHPSESSID=' + res_.cookies['PHPSESSID'],
        #     'referer': url,
        #     'sec-fetch-mode': 'no-cors',
        #     'sec-fetch-site': 'same-origin',
        #     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        # }
        for passwd in passwd_set:
            data = {
                'url': website_url,
                'ga': 1,
                't': 2,
                'p': passwd,
            }
            res_ = sess_.post(website_url, data = data)
            if res_.status_code == 200:
                res_ = sess_.get(resource_url)
                if len(res_.content) > 10000: # content is large enough to be an image
                    with open('test_img.jpg', 'wb') as f:
                        f.write(res_.content)
                    return passwd
        return 

    elif media_type == 'mov':      
        url = "https://ppt.cc/mov/player.php"
        headers = {
        }

if __name__ == "__main__":
    html = get_html('dcard url')
    soup = bs(html, 'html.parser')
    # get_password(soup)
    nice_passwd = set()
    ret = download('img', 'img url', ['passwd'])
    if ret != None:
        nice_passwd.add(ret)
