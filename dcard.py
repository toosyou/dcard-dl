import requests
from bs4 import BeautifulSoup as bs

class Dcard:
    """
    Description:
        This object is for dcard API only, but with some extendability.
    """
    API_ROOT = 'https://www.dcard.tw/_api'
    POSTS = 'posts'
    self.article_links = []
    self.article_json = {} # id: json
    def __init__(self, mode='pop'):
        """
        Description:
            Create this object while getting popular posts' id.
        Args:
            mode(str): Using dcard API or deepcard api? Maybe should use enum type.
        """
        if mode == 'pop':
            self.article_links = self.get_pop()

    def get_pop(self, forums='sex'):
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


    def get_article_content(self, article_id):
        """
        Description:
            Using dcard API to get the target's content.
        Args:
            article_id(str): Just id -3-.
        Return:
            content(list[str]): Article content, split by spaces etc.
        """
        res = requests.get(API_ROOT + '/posts/' + article_id)
        if res.status_code == '200':
            self.article_json[article_id] = res.json()
            return res.json()["Content"].split()
        elif res.status_code == '404':
            return []

    def get_host_comments(self, article_id):
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
                comments.union(set(res_json['comment'].split()))
        
        # Regular comments
        for count in range(0, self.article_json[article_id]["commentCount"], 30):
            res = requests.get(API_ROOT + '/posts/' + article_id + '/comments?after='+str(count))
            for res_json in res.json():
                if res_json['host'] == True and res_json['hidden'] == False:
                    comments.union(set(res_json['comment'].split()))
        
        return comment

    def get_short_links(self, content, regex):
        # res = requests.get(API_ROOT + '/posts/' + )
        """
        Description:
            Parse short links in content(depends on regex).
            Example of regex:
                re.compile('.*ppt\.cc.*')
                re.compile('.*risu\.io/[a-zA-Z]+')
        Args:
            content(list[str]): Each element contains single line of the whole content.
        Return:
            links(set): List including short links.
        """
        links = set()
        for line in content:
            if regex.match(line):
                links.add(line)
        
        return links

    def get_html(url):
        """
        Args:
            url(str): target dcard article url
        Return:
            html(str): html text
        """
        ui(f'get_html: {url}')
        res = requests.get(url)
        if res.status_code == 200:
            return res.text
        else:
            raise Exception(f'URL {url} unreachable.')
