#!/usr/bin/env python

import os
import json
import requests
import redis
import pprint

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
API_ROOT = 'https://bbs.net9.org:8080'
BOARD_NAME = os.getenv('BOARD_NAME', 'bbs_dev')
BATCH_SIZE = 32
MAKER_URL = 'https://maker.ifttt.com/trigger/%s/with/key/%s'
EVENT_NAME = 'maelstrom9'


def main():
    db = redis.from_url(REDIS_URL)
    last_post_offset = db.hget("offset", BOARD_NAME)
    all_users = db.hgetall("user_maker_key")
    if not last_post_offset:
        last_post_offset = 1
    last_post_offset = int(last_post_offset)
    roar_token = json.loads(db.hget("user_token", 'Roar'))
    params = {'session': roar_token['access_token'],
              'name': BOARD_NAME,
              'mode': 'normal',
              'start': last_post_offset,
              'count': BATCH_SIZE}
    posts = requests.get(API_ROOT + '/board/post_list', params=params).json()
    db.hincrby('offset', BOARD_NAME, len(posts))
    for post in posts:
        if post['owner'] in all_users:
            body = {'value1': BOARD_NAME, 'value2': post['title'], 'value3': 'http://www.rowell9.com/#'}
            resp = requests.post(MAKER_URL % (EVENT_NAME, all_users[post['owner']]), data=body)
            pprint.pprint(resp.text)


if __name__ == '__main__':
    main()
