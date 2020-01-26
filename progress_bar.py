import time
import sys

class Progress_Bar():
    def __init__(self):
        self.i = 0.0
        self.info = ''

    def bar(self, i):
        sys.stdout.write('\r')
        self.i = i
        i = int(i*100)
        sys.stdout.write("[%-10s] %d%% " % ('='*(i//10), i))
        sys.stdout.flush()

    def bar_with_info(self, info):
        sys.stdout.write('\r')
        i = int(self.i*100)
        sys.stdout.write("[%-10s] %d%% %s\n" % ('='*(i//10), i, info))
        sys.stdout.flush()
