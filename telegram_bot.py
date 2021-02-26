import os
import re
import configparser
from glob import glob
import json
import time

from tqdm import tqdm
from tinydb import TinyDB, Query
import telegram
from telegram import Bot
from telegram import InputMediaPhoto, InputMediaVideo, InputMediaAudio
from telegram.utils.helpers import escape_markdown

import better_exceptions; better_exceptions.hook()

db = TinyDB('./data/db.json')

parser = configparser.ConfigParser()
parser.read('./telegram.ini')

TOKEN = parser['bot']['token']
CHAT_ID = parser['group']['chat_id']
MEDIA_DIR = parser['media']['basedir']

class MediaGroup():
    def __init__(self, media_filenames, info):
        self.media_filenames = media_filenames
        self.info = info

def get_media_groups(basedir=MEDIA_DIR):
    dirs = [file_or_dir
                for file_or_dir in os.listdir(basedir)
                if os.path.isdir(os.path.join(basedir, file_or_dir))]

    groups = list()
    for dir in dirs:
        try:
            with open(os.path.join(basedir, dir, 'article.json'), 'r') as f:
                info = json.load(f)
        except:
            continue

        media_filenames = list()
        for support_type in ['jpg', 'jpeg', 'mp4', 'png']:
            media_filenames += glob(os.path.join(basedir, dir, '*.{}'.format(support_type)))

        groups.append(MediaGroup(media_filenames, info))

    return groups

def remove_posted(groups):
    media_entity = Query()

    for group in groups:
        for media_filename in list(group.media_filenames):
            if len(db.search(media_entity.filename == os.path.basename(media_filename))) > 0:
                group.media_filenames.remove(media_filename)

    groups = [group for group in groups if len(group.media_filenames) != 0]
    return groups

def remove_male_post(groups):
    groups = [group for group in groups if group.info['gender'] == 'F']
    return groups

def remove_empty_files(groups):
    for group in groups:
        for media_filename in list(group.media_filenames):
            if os.stat(media_filename).st_size == 0:
                group.media_filenames.remove(media_filename)
    groups = [group for group in groups if len(group.media_filenames) != 0]
    return groups

def post(bot, groups, chat_id=CHAT_ID):
    def remove_link(content):
        content = re.sub(r'https?:\/\/(?:\w+\.)?imgur\.com\/(?:\S*)(?:\.[a-zA-Z]{3,4})', '', content)
        content = re.sub(r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))", '', content)
        content = re.sub(r'\n+', ' ', content)
        return content

    for group in tqdm(groups):
        group.media_filenames = group.media_filenames[:9] if len(group.media_filenames) >= 10 else group.media_filenames
        photo_files = [open(fn, 'rb') for fn in group.media_filenames if re.match(r'.*\.(jpg|jpeg|png)', fn)]
        video_files = [open(fn, 'rb') for fn in group.media_filenames if re.match(r'.*\.mp4', fn)]

        has_private_content = any([re.match(r'.*_.*', fn) for fn in group.media_filenames])

        info = group.info
        caption = '[{}]({})\n'.format(escape_markdown(info['title'], version=2),
                                            'https://dcard.tw/f/sex/p/{}'.format(info['id']))
        caption += escape_markdown('#文章ID{} '.format(info['id']), version=2)
        caption += escape_markdown('#隱藏照片' if has_private_content else '', version=2)
        caption += '\n'
        caption += escape_markdown('{}'.format(remove_link(info['content'])).replace('\\', ''), version=2)
        caption = caption[:min(len(caption), 140)]

        medias = [InputMediaPhoto(pf) for i, pf in enumerate(photo_files)]
        medias += [InputMediaVideo(vf) for vf in video_files]

        medias[0].caption = caption
        medias[0].parse_mode = 'MarkdownV2'

        retry_counter = 0
        while True:
            try:
                bot.send_media_group(chat_id, medias, timeout=300)
            except telegram.error.NetworkError as e:
                print('Error:', caption, e, retry_counter)
                retry_counter += 1
                if retry_counter < 5:
                    time.sleep(30)
                    continue
            except telegram.error.RetryAfter as e:
                time.sleep(30)
                continue
            break

        for f in [*photo_files, *video_files]:
            db.insert({'filename': os.path.basename(f.name)})
            f.close()

        time.sleep(30)

if __name__ == '__main__':
    bot = Bot(TOKEN)
    groups = get_media_groups()
    groups = remove_posted(groups)
    groups = remove_male_post(groups)
    groups = remove_empty_files(groups)
    post(bot, groups)
