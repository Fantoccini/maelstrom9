#!/usr/bin/env python

import os
import json
import requests
import redis
import pprint
import time

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
API_ROOT = 'https://bbs.net9.org:8080'
BOARD_NAME = os.getenv('BOARD_NAME', 'bbs_dev')
BATCH_SIZE = 32
MAKER_URL = 'https://maker.ifttt.com/trigger/%s/with/key/%s'
EVENT_NAME = 'maelstrom9'
REDIRECT_URL = 'http://9.svbeeqv.com/auth'


def main():
    db = redis.from_url(REDIS_URL)
    last_post_offset = db.hget("offset", BOARD_NAME)
    all_users = db.hgetall("user_maker_key")
    if not last_post_offset:
        last_post_offset = 1
    last_post_offset = int(last_post_offset)
    roar_token = json.loads(db.hget("user_token", 'Roar'))
    if time.time() % 2592000 < 600:
        params = {
            'redirect_uri' : REDIRECT_URL,
            'grant_type': 'refresh_token',
            'refresh_token' : roar_token['refresh_token'],
            'client_id': db.hget('config', 'client_id'),
            'client_secret': db.hget('config', 'client_secret')
        }
        r = requests.get(API_ROOT + '/auth/token', params=params)
        roar_token = r.json()
        db.hset("user_token", 'Roar', json.dumps(roar_token))
    params = {'session': roar_token['access_token'],
              'name': BOARD_NAME,
              'mode': 'normal',
              'start': last_post_offset,
              'count': BATCH_SIZE}
    try:
        r = requests.get(API_ROOT + '/board/post_list', params=params)\
        posts = r.json()
    except ValueError:
        print r.text
        return
    db.hincrby('offset', BOARD_NAME, len(posts))
    for post in posts:
        if post['owner'] in all_users:
            body = {'value1': BOARD_NAME, 'value2': post['title'], 'value3': 'http://www.rowell9.com/'}
            resp = requests.post(MAKER_URL % (EVENT_NAME, all_users[post['owner']]), data=body)
            pprint.pprint(resp.text)


if __name__ == '__main__':
    main()
