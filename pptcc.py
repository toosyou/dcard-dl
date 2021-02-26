import requests
from bs4 import BeautifulSoup as bs

def pptcc_dl(folder: str, url: str, priority_passwd: set, passwd_set: set):
    """
    Return:
        passwd(str): nice passwd
        type(str): content type
    """

    website_url = url
    resource_url = url + '@.jpg'
    data = {
        'url': website_url,
        'ga': 1,
        't': 2,
        'p': '',
    }
    with requests.Session() as sess_:
        for passwd in [*priority_passwd, *passwd_set]:
            try:
                data['p'] = passwd
                res = sess_.post(website_url, data=data)
                soup = bs(res.text, 'html.parser')
                passwd_error_situation = [
                    'alert("請輸入您的通關密碼!");history.go(-1)', 'alert(\"您輸入的密碼並不正確，請再做檢查!\");history.go(-1)'
                ]
                if res.status_code == 200 and soup.find('script').text not in passwd_error_situation:
                    res = sess_.get(resource_url)
                    # content is large enough to be an image or larger than default image(48373)
                    if len(res.content) != 48373:
                        passwd_ = str(passwd)
                        with open(folder+url.split('/')[-1]+'_'+passwd_+'.jpg', 'wb') as f:
                            f.write(res.content)

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
                continue
            except Exception as e:
                raise e
        return None, None

if __name__ == "__main__":
    pptcc_dl('data/', 'https://ppt.cc/fb1Kdx', set(), set(['1102']))
    pass