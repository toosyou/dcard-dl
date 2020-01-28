import requests
import progress_bar
import threading
import queue
import datetime

num = 8
history = set()

class Worker(threading.Thread):
    def __init__(self, queue, lock):
        threading.Thread.__init__(self)
        self.queue = queue
        self.lock = lock
        self.total = self.queue.qsize()
        self.pb = progress_bar.Progress_Bar()
    
    def run(self):
        while self.queue.qsize() > 0:
            msg = self.queue.get()
            year, month, date, time = msg.split(',')
            self.get_api(year, month, date, time)
            
    def get_api(self, year, month, date, time):
        global history
        url = "https://tw.observer/api/posts?hot=0&before=" + \
            "{:04}-{:02}-{:02}T{:02}".format(int(year), int(month), int(date), int(time)) + \
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
        self.pb.bar((self.total - self.queue.qsize())/self.total)
        self.lock.release()


def get_articles(start_time, end_time):
    print(f'Try to using deepcard api...')
    sess = requests.Session()
    total = (1)*31*24
    counter = 0
    mission_queue = queue.Queue()
    time_delta = end_time - start_time
    current_time = start_time
    for i in range(time_delta.days + 1):
        for time in range(0, 24):
            counter += 1
            mission_queue.put(current_time.strftime("%Y,%m,%d")+f",{time:02d}")
        current_time += datetime.timedelta(days=1)

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
    get_articles(datetime.datetime(2019, 1, 27), datetime.datetime(2019,1,27))
