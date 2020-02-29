import os
import json
import requests
from bs4 import BeautifulSoup as bs


def dl(sess, folder, url, passwd, file_info):
    file_path = file_info['file_path']
    file_type = file_info['content_type']
    
    with open(folder+url.split('/')[-1]+'_'+passwd+'.'+file_type.split('/')[-1], 'wb') as f:
        res = sess.get(file_path, verify=False, stream=True)
        for chunk in res:
            f.write(chunk)
    # print(file_path, file_type)

    return passwd, file_type


def get_risu_dl_link(folder: str, url: str, passwd: str) ->str:
    """
    url(str): risu.io file url
    """
    headers = {
            # 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            # 'accept-encoding': 'gzip, deflate, br',
            # 'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            # 'cache-control': 'max-age=0',
            # 'if-none-match': 'W/"671fcaf288cda14a79cdded6bbf7580b"',
            # 'referer': 'https://risu.io/',
            # 'sec-fetch-mode': 'navigate',
            # 'sec-fetch-site': 'same-origin',
            # 'sec-fetch-user': '?1',
            # 'upgrade-insecure-requests': '1',
            # 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    }
    requests.urllib3.disable_warnings()
    with requests.Session() as sess:
        res = sess.get(url, headers = headers, verify=False)

        if res.status_code == 200:
            soup = bs(res.text, 'html.parser')
            
            app = soup.select('#app')
            if app:
                params = json.loads(next(app[0].children)[':params'])
                print(params)
                if params['lock'] == False: # if no password needed
                    for file_info in params['file_infos']
                    # file_info = params['file_infos']
                        passwd, file_type = dl(sess, folder, url, 'NOPASSWD', file_info)
                    return 'NOPASSWD', file_type

            result = soup.select('meta[name=csrf-token]')
            if result:
                csrf_token = result[0]['content']
                headers['x-csrf-token'] = csrf_token
            res = sess.post(url+'/confirm.json', headers = headers, data={'password': str(passwd)}, verify=False)

            if res.status_code == 200 and 'is_expired' in res.json():
                return None, 'is_expired'
            elif res.status_code == 200 and res.json()['lock'] == True:
                for file_info in res.json()['file_infos']:
                # file_info = res.json()['file_infos'][0]
                    passwd, file_type = dl(sess, folder, url, passwd, file_info)
                return passwd, file_type
            elif res.status_code == 200 and res.json()['lock'] == False:
                return None, 'wrong_passwd'
            else:
                return None, res.status_code
        else:
            print(res.status_code, url)
            return None, 'connection_error'


def risuio_dl(folder, url, priority_passwd, passwd_set):
    for passwd in [*priority_passwd, *passwd_set]:
        ret, content_type = None, None
        try:
            ret, content_type = get_risu_dl_link(folder, url, passwd)
            if ret:
                return ret, content_type
            elif content_type == 'wrong_passwd':
                continue
            elif content_type == 'is_expired':
                return None, content_type
            elif content_type == 'connection_error':
                return None, content_type
            else:
                print(content_type)
                return None, content_type
        except Exception as e:
            raise e
            return None, None
    return None, None

if __name__ == "__main__":
    pass
