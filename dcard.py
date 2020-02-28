import re
import requests

import time
import random
import threading

import risu
import deepcard
import progress_bar

def get_pop(forums='sex'):
    """
    Description:
        Get pop posts' id.
    Args:
        forums(str): Target forums
    Return:
        article_links(list[str]): Pop posts' id.
    """ 
    return list(map(lambda a: str(a['id']), requests.get(
        API_ROOT + '/forums/' + forums + '/posts?popular=true&limit=30'
    ).json()))


class Dcard:
    """
    Description:
        This object is for dcard API only, but with some extendability.
        One object for one dcard link(site).
    """
    API_ROOT = 'https://www.dcard.tw/_api'

    self.article_links = []
    self.article_json = None
    self.exist = False
    self.article_json = None
    self.text_by_host = None
    self.short_links  = {}
    self.passwd = set()

    def __init__(self, article_id, mode='pop'):
        """
        Description:
            Create this object while getting popular posts' id.
        Args:
            mode(str): Using dcard API or deepcard api? Maybe should use enum type.
        """
        if mode == 'pop':
            self.article_links = self.get_pop() # This may need to parallelize
        res = requests.get(API_ROOT + '/posts/' + article_id)

        if res.status_code == '200':
            self.exist = True
        elif res.status_code == '404':
            self.exist = False
        else:
            print(res.status_code)

        if self.exist:
            self.article_json = res.json()
            article_content = self.article_json["content"].split()
            host_comments   = self.get_host_comments() # depends on commentCount
            self.text_by_host = article_content.union(host_comments)
            self.short_links = {
                'risu.io': self.get_short_links(re.compile('.*risu\.io/[a-zA-Z]+')),
                'ppt.cc':  self.get_short_links(re.compile('.*ppt\.cc.*')),
            }
            self.passwd = self.get_password()


    def get_host_comments(self, article_id=self.article_id):
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
        res = requests.get(API_ROOT + '/posts/' + article_id + '/comments?popular=true')
        # Post by host and available
        for res_json in res.json():
            if res_json['host'] == True and res_json['hidden'] == False:
                comments = comments.union(set(res_json['comment'].split()))
        
        # Regular comments
        for count in range(0, self.article_json[article_id]["commentCount"], 30):
            res = requests.get(API_ROOT + '/posts/' + article_id + '/comments?after='+str(count))
            for res_json in res.json():
                if res_json['host'] == True and res_json['hidden'] == False:
                    comments = comments.union(set(res_json['comment'].split()))
        
        return comment


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


    def get_password():
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
                condidate_passwd = pattern.sub('', text)
                passwd_set.add(candidate_passwd)
        
        year, month, day = self.article_json['createAt'].split('T')[0].split('-')
        for date_shift in range(4): # Maybe try createAt -> updateAt
            date = (datetime.date(year, int(month), int(day))+datetime.timedelta(days=date_shift)).strftime('%m%d')
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

    def __init__(self, queue, lock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.total = self.queue.qsize()
        self.total_links = 1 # prevent divide by zero error
        self.success_links = 0
        self.is_expired = 0

    def run(self):
        # Get services status
        service_status = {
            'ppt.cc': False,
            'risu.io': False,
        }
        if requests.get('https://ppt.cc/').status_code == 200:
            service_status['ppt.cc'] = True
        if requests.get('https://risu.io/', verify=False).status_code == 200:
            service_status['risu.io'] = True
        
        while self.queue.qsize() > 0:
            with open(folder + 'this_dl.log', 'a') as log:
                # Accept job from queue
                article_id = self.queue.get()
                # Create Dcard object
                dcard = Dcard(article_id)
                if dcard.exist == False:
                    continue

                priority_passwd = set()
                self.total_links = len(dcard.short_links['ppt.cc'])*service_status['ppt.cc'] + \
                                   len(dcard.short_links['risu.io'])*service_status['risu.io']
                for service, short_url in dcard.short_links.items():
                    for url in short_url:
                        ret, content_type = None, None
                        try:
                            if service == 'risu.io':
                                ret, content_type = risu.risuio_dl(
                                    folder, short_url, priority_passwd, passwd_set 
                                )
                            # if service == 'ppt.cc':
                            #     ret, content_type = pptcc_dl(
                            #         short_url, priority_passwd, passwd_set
                            #     )  # dl
                        except Exception as e:
                            self.lock.acquire()
                            print(e)
                            log.write(
                                u"[Unknown][\u001b[31mFailed\u001b[0m] " + f"{url} {short_url}\n")
                            pb.bar_with_info(u"[Unknown][\u001b[31mFailed\u001b[0m] " +
                                                f"{short_url}")
                            self.lock.release()
                            raise e

                        if ret:
                            # logging
                            self.success_links += 1
                            self.lock.acquire()
                            log.write(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m]" +
                                        f"{url} {short_url} {ret}\n")
                            pb.bar_with_info(f"[{content_type}]" + u"[\u001b[32mSuccess\u001b[0m] " +
                                                f"{short_url} {ret}")
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
                                f"{url} {short_url}\n"
                            )
                            pb.bar_with_info(
                                f"[{content_type if content_type else 'Unknown'}]" +
                                u"[\u001b[31mFailed\u001b[0m] " +
                                f"{short_url}"
                            )
                            self.lock.release()


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
    if args.range:
        time_range = list(map(int, args.range.split('_')))
        start_time = datetime.date(*time_range[:3])
        end_time   = datetime.date(*time_range[3:])
        args.current = False
    worker_num = args.thread

    # Main steps
    if args.current == True:
        article_links = get_pop()
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
            workers.append(Worker(mission_queue, lock))
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