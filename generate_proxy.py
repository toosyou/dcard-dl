import re
import requests
import json
import asyncio
from proxybroker import Broker

def get_proxy_from_spys_one():
    base_url = 'http://spys.me/proxy.txt'
    r = requests.get(base_url)
    ip_and_ports = re.findall(r'((?:[0-9]{1,3}\.){3}[0-9]{1,3}\:[0-9]{1,4}) [A-Z]{1,3}\-[A-z]\-S', r.text)

    proxy_list = list()
    for ipp in ip_and_ports:
        proxy_list.append({
            'proxy': {
                'https': ipp
        }})

    with open('spys_one_proxy.json', 'w') as f:
        json.dump(proxy_list, f)

proxy_list = list()
async def show(proxies):
    global proxy_list
    while True:
        proxy = await proxies.get()
        if proxy is None: break
        print('Found proxy: %s' % proxy)

        proxy = str(proxy)
        proxy_list.append({
            'response_time': float(re.findall(r'([0-9]+\.[0-9]+)s', proxy)[0]),
            'proxy': {
                'https': re.findall(r'((?:[0-9]{1,3}\.){3}[0-9]{1,3}\:[0-9]{1,4})', proxy)[0]
        }})

        proxy_list = [pl for pl in proxy_list if pl['response_time'] < 2]
        with open('proxy.json', 'w') as f:
            json.dump(proxy_list, f)

if __name__ == "__main__":
    get_proxy_from_spys_one()

    proxies = asyncio.Queue()
    broker = Broker(proxies)
    tasks = asyncio.gather(
        broker.find(types=['HTTPS'],
                    limit=100),
        show(proxies))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(tasks)


