import re
import json
import requests

import os
import time
import random
import datetime
import queue
import threading
import argparse
import pathlib

import risu
import pptcc
import deepcard
import progress_bar

def get_pop(proxy, forums='sex'):
    """
    Description:
        Get pop posts' id.
    Args:
        forums(str): Target forums.
    Return:
        article_links(list[str]): Pop posts' id.
    """ 
    return list(map(lambda a: str(a['id']), requests.get(
        Dcard.API_ROOT + '/forums/' + forums + '/posts?popular=true&limit=30',
        proxies = proxy
    ).json()))

def create_folder(folder):
    """
    Description:
        Create folder in case you don't have it -3-.
    Args:
        folder(str): Folder path.
    Return:
        Nope :D
    """
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

class Dcard:
    """
    Description:
        This object is for dcard API only, but with some extendability.
        One object for one dcard link(site).
    """
    API_ROOT = 'https://www.dcard.tw/_api'

    def __init__(self, article_id, proxy, mode='pop'):
        """
        Description:
            Create this object while getting popular posts' id.
        Args:
            mode(str): Using dcard API or deepcard api? Maybe should use enum type.
        """
        self.article_id = article_id
        self.proxy = proxy

        res = requests.get(
            Dcard.API_ROOT + '/posts/' + article_id,
            proxies = self.proxy
        )

        self.exist = False
        if res.status_code == 200:
            self.exist = True
        else:
            print(res.status_code)

        if self.exist:
            self.article_json = res.json()
            article_content = set(self.article_json["content"].split())
            host_comments   = self.get_host_comments() # depends on commentCount
            self.text_by_host = article_content.union(host_comments)
            self.short_links = {
                'risu.io': self.get_short_links(re.compile('.*risu\.io/[a-zA-Z]+')),
                'ppt.cc':  self.get_short_links(re.compile('.*ppt\.cc.*')),
            }
            self.passwd = self.get_password()


    def get_host_comments(self):
        """
        Description:
            Get comments send by host.
        Args:
            article_id(str): Just id -3-.
        Return:
            content(set[str]): Comments' content, split by spaces etc.
        """
        comments = set()

        # Popular comments
        res = requests.get(
            Dcard.API_ROOT + '/posts/' + self.article_id + '/comments?popular=true',
            proxies = self.proxy
        )
        # Post by host and available
        for res_json in res.json():
            if res_json['host'] == True and res_json['hidden'] == False:
                comments = comments.union(set(res_json['content'].split()))
        
        # Regular comments
        for count in range(0, self.article_json["commentCount"], 100):
            # Be kind to Dcard API
            time.sleep(random.random() + 1)

            res = requests.get(
                Dcard.API_ROOT + '/posts/' + self.article_id + '/comments?limit=100&after='+str(count),
                proxies = self.proxy
            )
            for res_json in res.json():
                if res_json['host'] == True and res_json['hidden'] == False:
                    comments = comments.union(set(res_json['content'].split()))
        
        return comments


    def get_short_links(self, regex):
        """
        Description:
            Parse short links in content(depends on regex).
            Example of regex:
                re.compile('.*ppt\.cc.*')
                re.compile('.*risu\.io/[a-zA-Z]+')
        Args:
            content(set[str]): Each element contains single line of the whole content.
        Return:
            links(set): List including short links.
        """
        links = set()
        for line in self.text_by_host:
            if regex.match(line):
                links.add(line)
        
        return links


    def get_password(self):
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
        out = re.compile("http|(b|B[0-9]+)")
        pattern = re.compile("[-|#|＃|「|」|=|:|：|(Password)|(password)|(密碼)]")
        passwd_set = set()
        for text in self.text_by_host:
            if not out.match(text):
                candidate_passwd = pattern.sub('', text)
                passwd_set.add(candidate_passwd)
        
        year, month, day = self.article_json['createdAt'].split('T')[0].split('-')
        for date_shift in range(4): # Maybe try createdAt -> updatedAt
            date = (datetime.date(int(year), int(month), int(day))+datetime.timedelta(days=date_shift)).strftime('%m%d')
            passwd_set.add(date)
        
        passwd_set = passwd_set.union(set(self.article_json['tags']))
        passwd_set = passwd_set.union(set(self.article_json['topics']))
        passwd_set = passwd_set.union({'0000', '1234', '4321'})
        try:
            passwd_set.remove('') # prevent empty passwd
        except: # if already nice
            pass

        return passwd_set
    

class Worker(threading.Thread):

    pb = progress_bar.Progress_Bar()

    def __init__(self, folder, queue, proxy, lock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.total = self.queue.qsize()
        self.total_links = 0
        self.success_links = 0
        self.is_expired = 0
        self.folder = folder
        self.proxy = proxy

    def run(self):
        # Get services status
        service_status = {
            'ppt.cc': False,
            'risu.io': False,
        }
        requests.urllib3.disable_warnings() # for risu.io
        if requests.get('https://ppt.cc/').status_code == 200:
            service_status['ppt.cc'] = True
        if requests.get('https://risu.io/', verify=False).status_code == 200:
            service_status['risu.io'] = True
        
        while self.queue.qsize() > 0:
            with open(self.folder + 'this_dl.log', 'a') as log:
                # Accept job from queue
                article_id = self.queue.get()
                # Be kind to dcard'api
                # Sleep after get id from queue, in case of 
                # calling `.get()` to an empty queue
                time.sleep(random.random() + 1)
                # Create Dcard object
                try:
                    dcard = Dcard(article_id, self.proxy)
                except Exception as e:
                    print("Proxy Connection Error.")
                    self.queue.put(article_id)
                    continue
                
                if dcard.exist == False:
                    continue

                priority_passwd = set()
                self.total_links += len(dcard.short_links['risu.io'])*service_status['risu.io'] + \
                                    len(dcard.short_links['ppt.cc'])*service_status['ppt.cc']
                                   
                for service, short_url in dcard.short_links.items():
                    for url in short_url:
                        ret, content_type = None, None
                        try:
                            if service == 'risu.io':
                                ret, content_type = risu.risuio_dl(
                                    self.folder, url, priority_passwd, dcard.passwd 
                                )
                            if service == 'ppt.cc':
                                ret, content_type = pptcc.pptcc_dl(
                                    self.folder, url, priority_passwd, dcard.passwd
                                )  # dl
                        except Exception as e:
                            self.lock.acquire()
                            print(e)
                            log.write(
                                u"[Unknown][\u001b[31mFailed\u001b[0m] " + f"{dcard.article_id} {url}\n")
                            Worker.pb.bar_with_info(u"[Unknown][\u001b[31mFailed\u001b[0m] " +
                                                f"{url}")
                            self.lock.release()
                            raise e

                        if ret:
                            # logging
                            self.success_links += 1
                            self.lock.acquire()
                            log.write(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m]" +
                                        f"{dcard.article_id} {url} {ret}\n")
                            Worker.pb.bar_with_info(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m] " +
                                                f"{url} {ret}")
                            # optimize
                            priority_passwd.add(ret)
                            self.lock.release()
                        else:
                            # logging
                            self.lock.acquire()
                            if content_type == 'is_expired':
                                self.total_links -= 1
                                self.is_expired  += 1
                            log.write(
                                f"[{content_type if content_type else 'Unknown'}]" + 
                                u"[\u001b[31mFailed\u001b[0m] " + 
                                f"{dcard.article_id} {url}\n"
                            )
                            Worker.pb.bar_with_info(
                                f"[{content_type if content_type else 'Unknown'}]" +
                                u"[\u001b[31mFailed\u001b[0m] " +
                                f"{url}"
                            )
                            self.lock.release()

                self.lock.acquire()
                Worker.pb.bar((self.total - self.queue.qsize())/self.total)
                self.lock.release()
        print("A worker has got off work.")


if __name__ == "__main__":
    # Preset
    folder = './current_' + datetime.date.today().strftime('%Y_%m_%d')
    start_time = datetime.date(2019, 12, 1)
    end_time = datetime.date(2020, 1, 1)
    worker_num = 4
    lock = threading.Lock()

    parser = argparse.ArgumentParser()
    time_group = parser.add_mutually_exclusive_group()
    time_group.add_argument('-c', '--current', help='current Dcard site result', action='store_true', default=True)
    time_group.add_argument('-r', '--range', help='set range(use deepcard api) format: YYYY_MM_DD_YYYY_MM_DD')
    parser.add_argument('-f', '--folder', help='set folder path(will auto-generate it for u)')
    parser.add_argument('-t', '--thread', help='default = 4', type=int, default=4)
    args = parser.parse_args()
    folder = args.folder or folder
    folder = os.path.join('./', folder, '')
    # Create folder
    create_folder(folder)

    if args.range:
        time_range = list(map(int, args.range.split('_')))
        start_time = datetime.date(*time_range[:3])
        end_time   = datetime.date(*time_range[3:])
        args.current = False

    worker_num = args.thread
    # Use proxy
    try:
        with open('proxy.json', 'r') as j:
            proxy = json.loads(j.read())
            if len(proxy) > 0:
                select = random.randint(1, len(proxy)) - 1
                select_proxy = proxy[select]['proxy']

    except FileNotFoundError as e:
        print('Proxy configure file not found.')

    # Main steps
    if args.current == True:
        article_links = get_pop(select_proxy)
    if args.range:
        article_links = deepcard.get_articles(start_time, end_time)
    
    total_links = 0
    success_links = 0
    expired_links = 0
    mission_queue = queue.Queue()
    workers = []

    with open(folder + 'this_dl.log', 'w') as log:
        for link in article_links:
            mission_queue.put(link)
        for i in range(worker_num):
            workers.append(Worker(folder, mission_queue, select_proxy, lock))
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        for worker in workers:
            total_links += worker.total_links
            success_links += worker.success_links
            expired_links += worker.is_expired
        
        print(f"Total links: {total_links}")
        print(f"Expired links: {expired_links}")
        print(f"Success links: {success_links}")
        print(f"Success rate: {success_links/total_links}")