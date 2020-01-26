import requests
import progress_bar
import threading
import queue

num = 8
history = set()

class Worker(threading.Thread):
    def __init__(self, queue, lock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.total = self.queue.qsize()
    
    def run(self):
        while self.queue.qsize() > 0:
            msg = self.queue.get()
            month, date, time = msg.split(',')
            self.get_api(month, date, time)
            
    def get_api(self, month, date, time):
        global history
        url = "https://tw.observer/api/posts?hot=0&before=2019-" + \
            "{:02}-{:02}T{:02}".format(int(month), int(date), int(time)) + \
            "%3A00%3A00.000000Z&term=%EF%BC%83%E8%A5%BF%E6%96%AF"
        res = requests.Session().get(url)
        __history = set()
        if res.status_code == 200:
            res_json = res.json()
            for article in res_json['data']['posts']:
                if article['likeCount'] >= 100:
                    __history.add(str(article['id']))
        self.lock.acquire()
        history = history.union(__history)
        progress_bar.bar((self.total - self.queue.qsize())/self.total)
        self.lock.release()


def get_articles():
    print(f'Try to using deepcard api...')
    sess = requests.Session()
    total = (5-3)*31*24
    counter = 0
    mission_queue = queue.Queue()
    for month in range(1, 3):
        for date in range(1, 32):
            for time in range(0, 24):
                counter += 1
                mission_queue.put(f"{month:02d},{date:02d},{time:02d}")

    workers = []
    lock = threading.Lock()
    for worker_num in range(num):
        workers.append(Worker(mission_queue, lock))
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    
    print(len(history))
    return history


def get_articles_():
    print(f'Try to using deepcard api...')
    sess = requests.Session()
    history = set()
    total = (5-3)*31*24
    counter = 0
    pb = progress_bar.Progress_Bar()
    for month in range(3, 5):
        for date in range(1, 32):
            for time in range(0, 24):
                counter += 1
                pb.bar(counter/total)
                url = "https://tw.observer/api/posts?hot=0&before=2019-" + \
                    "{:02}-{:02}T{:02}".format(month, date, time) + \
                      "%3A00%3A00.000000Z&term=%EF%BC%83%E8%A5%BF%E6%96%AF"
                res = sess.get(url)
                if res.status_code == 200:
                    res_json = res.json()
                    for article in res_json['data']['posts']:
                        if article['likeCount'] >= 100:
                            history.add(str(article['id']))
    print(len(history))
    return history
if __name__ == "__main__":
    get_articles_()
