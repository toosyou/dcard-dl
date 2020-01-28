import os
import re
import time
import queue
import random
import pathlib
import requests
import argparse
import threading
import concurrent.futures
from bs4 import BeautifulSoup as bs

import deepcard
import progress_bar

import datetime

sess = requests.Session()
folder = './beta_2020_01_28/'
start_time = datetime.datetime(2020, 1, 28)
end_time = datetime.datetime(2020, 1, 28)
worker_num = 4
lock = threading.Lock()

class Worker(threading.Thread):
    pb = progress_bar.Progress_Bar()

    def __init__(self, queue, lock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.total = self.queue.qsize()
        self.total_links = 0
        self.success_links = 0

    def run(self):
        while self.queue.qsize() > 0:
            with open(folder + 'dl.log', 'a') as log:
                link = self.queue.get()
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
                self.total_links += len(pptcc_links)
                pptcc_workers = []
                for test_purpose in range(1): #  for test purpose, switch to linear version
                    for pptcc_url in pptcc_links:
                        ret, content_type = None, None
                        try:
                            ret, content_type = download_process(
                                pptcc_url, priotiry_passwd, passwd_set)  # dl
                # with concurrent.futures.ThreadPoolExecutor() as executor:
                #     future_to_url = {
                #         executor.submit(download_process, pptcc_url, priotiry_passwd, passwd_set): pptcc_url for pptcc_url in pptcc_links
                #     }
                #     for future in concurrent.futures.as_completed(future_to_url):
                #         ret, content_type = None, None
                #         pptcc_url = future_to_url[future]
                #         try:
                #             ret, content_type = future.result() # get return values
                        except Exception as e:
                            self.lock.acquire()
                            print(e)
                            log.write(
                                u"[Unknown][\u001b[31mFailed\u001b[0m] " + f"{url} {pptcc_url}\n")
                            pb.bar_with_info(u"[Unknown][\u001b[31mFailed\u001b[0m] " +
                                            f"{pptcc_url}")
                            self.lock.release()
                    
                        if ret:
                            # logging
                            self.success_links += 1
                            self.lock.acquire()
                            log.write(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m]" +
                                    f"{url} {pptcc_url} {ret}\n")
                            pb.bar_with_info(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m] " +
                                            f"{pptcc_url} {ret}")
                            # optimize
                            priotiry_passwd.add(ret)
                            self.lock.release()
                        else:
                            # logging
                            self.lock.acquire()
                            log.write(
                                u"[Unknown][\u001b[31mFailed\u001b[0m] " + f"{url} {pptcc_url}\n")
                            pb.bar_with_info(u"[Unknown][\u001b[31mFailed\u001b[0m] " +
                                            f"{pptcc_url}")
                            self.lock.release()
                self.lock.acquire()
                pb.bar((self.total - self.queue.qsize())/self.total)
                self.lock.release()

def create_folder(folder):
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

def to_dict(string):
    string = string.strip()
    l = string.split('\n')
    ret_dict = {}
    for line in l:
        line = line.split(': ')
        if ':' not in line[0]:
            ret_dict[line[0]] = line[1]
    return ret_dict

pb = Worker.pb

def ui(customize_string):
    pb.bar_with_info(f'Try to {customize_string}...')

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
    # links = soup.find_all('a', href=re.compile('.*ppt\.cc.*'))
    links = set()
    post_content_links = soup.select('div[class*=Post_content] > div > div > div > div > a')
    for a in post_content_links:
        if 'ppt.cc' in a.text:
            links.add(a.text)
    post_authors = soup.select('span[class*=PostAuthor_root]')
    for post_author in post_authors:
        if post_author.text == '原PO':
            for parent in post_author.parents:
                if parent.name == 'header':
                    tmp = parent.parent.find_all('a', href=re.compile('.*ppt\.cc.*'))
                    if tmp:
                        links.add(tmp[0].text)
    return links


def search_reply(soup):
    ui(f'search_reply')
    reply_author = soup.select(".PostAuthor_root_3vAJfe")
    passwd_set = set()
    for author in reply_author:
        if '原PO' in author.text:
            tmp = author.find_parent('div', class_='CommentEntry_entry_3SaSrr').find(
                'div', class_='CommentEntry_content_1ATrw1').select('div > div > div')
            for block in tmp:
                for i in block.getText().split():
                    if 'https' not in i or not re.match('B[0-9]+', i): # delete href and B[0-9]+ replies
                        candidate_passwd = re.sub('[-|#|＃|「|」|=|:|：|(Password)|(password)|密碼]', '', i.strip()).strip()
                        passwd_set.add(candidate_passwd)  # replace all '-'
    return passwd_set


def get_password(soup):
    """
    - [v] Original Poster's replies(only rows)(replaced all '-' in search_reply)
    - [v] Dates (+3 date shift)
    - [v] Years
    - [v] Tags
    - [v] Post content
    - [v] delete B[0-9]+ replies
    - [v] Hashtags
    - [ ] Artificial
    - [ ] Natural language password hint
    """
    ui(f'get_password')
    passwd_set = search_reply(soup)  # replies

    date = re.findall('[0-9]*月[0-9]*日',
                      soup.select('span[class*=Post_date]')[0].text)[0]
    month, day = date[:-1].split('月')
    for date_shift in range(4):  # brute force date shift
        date = "{:02}".format(int(month)) + "{:02}".format(int(day)+date_shift)
        passwd_set.add(date)  # dates

    YEARS = ['2020', '2019', '2018', '2017']
    for years in YEARS:
        passwd_set.add(years)  # years

    for i in soup.select('div[class*=PostPage_content] a[class*=TopicList_topic]'):
        passwd_set.add(i.text)  # tags

    for i in soup.select('div[class*=Post_content] > div > div > div'):
        # post content without '-'
        passwd_set.add(i.text.strip().replace('-', ''))
    try:
        passwd_set.remove('')  # prevent empty passwd
    except:  # if already nice
        pass
    try:
        passwd_set = passwd_set.union({'0000', '1234', '4321'}) # artificial passwd
    except:
        pass
    passwd_set = set(map(lambda i: re.sub(
        '[-|#|＃|「|」|=|:|：|(Password)|(password)|密碼]', '', i.strip()).strip(), passwd_set))
    return passwd_set


def download_process(url, priority_passwd, passwd_set):  # download single pptcc resource(img or img+mov)
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
        try:
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
        except ConnectionError as e:
            print(e)
            time.sleep(1)
            continue
        except Exception as e:
            raise e
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
            ret_links.add(result[0].replace('/f/sex/p/', ''))
    return ret_links

def test_dl_all_img():
    ##  dcard site
    article_links = get_articles('https://www.dcard.tw/f/sex')

    ##  dcard api (unable to brute force, will be blocked)
    # article_links = list(map(lambda a: str(a['id']), requests.Session().get(
    #     'https://www.dcard.tw/_api/forums/sex/posts?popular=true&limit=30'
    # ).json()))

    ##  deepcard api
    # article_links = deepcard.get_articles(start_time, end_time)
    ##
    total_links = 0
    success_links = 0
    mission_queue = queue.Queue()
    workers = []
    
    with open(folder + 'dl.log', 'w') as log:
        for link in article_links:
            mission_queue.put(link)
        for i in range(worker_num):
            workers.append(Worker(mission_queue, lock))
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        for worker in workers:
            total_links += worker.total_links
            success_links += worker.success_links
        
        print(f"Total links: {total_links}")
        print(f"Success links: {success_links}")
        print(f"Success rate: {success_links/total_links}")


def concurrent_download_process(url, priority_passwd, passwd_set):
    """
    Return:
        passwd(str): nice passwd
        type(str): content type
    """
    ui(f'download_process {url}')
    target_passwd, target_type = None, None
    with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
        future_to_passwd = {executor.submit(try_passwd, url, passwd): passwd for passwd in [*priority_passwd, *passwd_set]}
        for future in concurrent.futures.as_completed(future_to_passwd):
            _passwd, _type = future.result()
            if _type != None:
                target_passwd, target_type = _passwd, _type
    return target_passwd, target_type


def try_passwd(url, passwd):
    sess_ = requests.Session()
    time.sleep(1)
    website_url = url
    resource_url = url + '@.jpg'
    data = {
        'url': website_url,
        'ga': 1,
        't': 2,
        'p': '',
    }
    
    try:
        data['p'] = passwd
        res_ = sess_.post(website_url, data=data)
        soup_ = bs(res_.text, 'html.parser')
        passwd_error_situation = [
            'alert("請輸入您的通關密碼!");history.go(-1)', 'alert(\"您輸入的密碼並不正確，請再做檢查!\");history.go(-1)']
        if res_.status_code == 200 and soup_.find('script').text not in passwd_error_situation:
            res_ = sess_.get(resource_url)  # Disable SSL verify
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
    except ConnectionError as e:
        print(e)
        # time.sleep(random.randint(1,3))
        # try_passwd(url, passwd)
    except Exception as e:
        raise e
    return None, None

if __name__ == "__main__":
    create_folder(folder)
    test_dl_all_img()
    # test_pptcc_links()
