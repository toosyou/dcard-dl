import re
import requests
import argparse
from itertools import combinations as cmb
from bs4 import BeautifulSoup as bs

sess = requests.Session()
folder = './beta_1/'


def ui(customize_string):
    print(f'Try to {customize_string}...')


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
    ui(f'get_html: {url}')
    res = sess.get(url)
    if res.status_code == 200:
        return res.text
    else:
        raise Exception(f'URL {url} unreachable.')


def get_pptcc_links(soup):
    """
    Args:
        soup(bs): BeautifulSoup object
    Return:
        links(set): ppt.cc links, str
    """
    ui(f'get_pptcc_links')
    links = soup.find_all('a', href=re.compile('.*ppt\.cc.*'))
    links = set(map(lambda a: a.text, links))
    return links


def search_reply(soup):
    ui(f'search_reply')
    reply_author = soup.select(".PostAuthor_root_3vAJfe")
    passwd_set = set()
    for author in reply_author:
        if '原PO' in author.text:
            tmp = author.find_parent('div', class_='CommentEntry_entry_3SaSrr').find(
                'div', class_='CommentEntry_content_1ATrw1').select('div > div > div')
            for i in tmp:
                if 'https' not in i.text:
                    passwd_set.add(i.text.strip().replace(
                        '-', ''))  # replace all '-'

    return passwd_set


"""
- [v] Original Poster's replies(only rows)(replaced all '-' in search_reply)
- [v] Dates
- [v] Years
- [v] Tags
- [v] Post content
"""


def get_password(soup):
    ui(f'get_password')
    passwd_set = search_reply(soup)  # replies

    date = re.findall('[0-9]*月[0-9]*日',
                      soup.select('span[class*=Post_date]')[0].text)[0]
    month, day = date[:-1].split('月')
    date = "{:02}".format(int(month)) + "{:02}".format(int(day))
    passwd_set.add(date)  # dates

    YEARS = ['2020', '2019', '2018', '2017']
    for years in YEARS:
        passwd_set.add(years)  # years

    for i in soup.select('div[class*=PostPage_content] a[class*=TopicList_topic]'):
        passwd_set.add(i.text)  # tags

    for i in soup.select('div[class*=Post_content] > div > div > div'):
        # post content without '-'
        passwd_set.add(i.text.strip().replace('-', ''))

    return passwd_set


def download_process(url, priority_passwd, passwd_set):
    """
    Return:
        passwd(str): nice passwd
        type(str): content type
    """
    ui(f'download_process {url}')
    sess_ = requests.Session()

    website_url = url
    resource_url = url + '@.jpg'
    data = {
        'url': website_url,
        'ga': 1,
        't': 2,
        'p': '',
    }
    for passwd in [*priority_passwd, *passwd_set]:
        data['p'] = passwd
        res_ = sess_.post(website_url, data=data)
        soup_ = bs(res_.text, 'html.parser')
        passwd_error_situation = [
            'alert("請輸入您的通關密碼!");history.go(-1)', 'alert(\"您輸入的密碼並不正確，請再做檢查!\");history.go(-1)']
        if res_.status_code == 200 and soup_.find('script').text not in passwd_error_situation:
            res_ = sess_.get(resource_url)
            # content is large enough to be an image or larger than default image(48373)
            if len(res_.content) != 48373:
                passwd_ = str(passwd)
                with open(folder+url.split('/')[-1]+'_'+passwd_+'.jpg', 'wb') as f:
                    f.write(res_.content)

                # try mov
                mov_sess = sess_
                mov_res = mov_sess.post(website_url, data=data)

                mov_res = mov_sess.get('https://www.ppt.cc/mov/player.php',
                                       headers={'referer': website_url, 'range': 'bytes=0-'})
                if mov_res.status_code == 206:
                    with open(folder+url.split('/')[-1]+'_'+passwd+'.mp4', 'wb') as f:
                        f.write(mov_res.content)
                        return passwd, 'mov'
                else:
                    return passwd, 'img'
    return None, None


def get_articles(url):
    ui(f'get_articles {url}')
    try:
        html = get_html(url)
    except Exception as e:
        raise e
    soup = bs(html, 'html.parser')
    articles = soup.select('main > div > div > div > a')
    ret_links = set()
    for link in articles:
        result = re.findall('/f/sex/p/[0-9]+', link['href'])  # spend times !!!
        if len(result) == 1:
            ret_links.add(result[0])
    return ret_links


def test_dl_all_img():
    ##  dcard site
    # article_links = get_articles('https://www.dcard.tw/f/sex')

    ##  dcard api
    article_links = list(map(lambda a: str(a['id']), requests.Session().get(
        'https://www.dcard.tw/_api/forums/sex/posts?popular=true&limit=30'
    ).json()))
    article_links.append('232936639')
    article_links.append('232947487')
    ##  deepcard api
    # article_links = set()
    # for i in range(1, 32):

    #     res.json()['data']['posts'][0]['id']

    ##
    total_links = 0
    success_links = 0
    with open(folder + 'dl.log', 'w') as log:
        for link in article_links:
            url = 'https://www.dcard.tw/f/sex/p/' + link
            try:
                html = get_html(url)
            except:
                print(f"Exception: URL {url} Unreachable.")
                continue
            # logging
            log.write(url + '\n')
            # parsing
            soup = bs(html, 'html.parser')
            pptcc_links = get_pptcc_links(soup)
            passwd_set = get_password(soup)
            priotiry_passwd = set()
            total_links += len(pptcc_links)
            for pptcc_url in pptcc_links:
                ret, content_type = download_process(
                    pptcc_url, priotiry_passwd, passwd_set)
                # print(ret, content_type)
                if ret:
                    # logging
                    success_links += 1
                    log.write(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m]" +
                              f"{pptcc_url} {ret}\n")
                    print(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m] " +
                          f"{pptcc_url} {ret}")
                    # optimize
                    priotiry_passwd.add(ret)
                else:
                    # logging
                    log.write(
                        u"[Unknown][\u001b[31mFailed\u001b[0m] " + f"{pptcc_url}\n")
                    print(u"[Unknown][\u001b[31mFailed\u001b[0m] " + f"{pptcc_url}")

        print(f"Total links: {total_links}")
        print(f"Success links: {success_links}")
        print(f"Success rate: {success_links/total_links}")


if __name__ == "__main__":
    test_dl_all_img()