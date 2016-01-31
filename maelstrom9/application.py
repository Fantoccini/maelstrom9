#!/usr/bin/env python
import os
import urllib
import requests
import json
import redis
import uuid
from flask import Flask, g, request, redirect, url_for, render_template, jsonify, make_response

application = Flask(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
API_ROOT = 'https://bbs.net9.org:8080'

application.secret_key = os.urandom(24)


@application.before_request
def before_request():
    g.db = redis.from_url(REDIS_URL)


@application.route('/auth')
def auth():
    params = {'redirect_uri': url_for('auth', _external=True),
              'grant_type': 'authorization_code',
              'code': request.args['code'],
              'client_id': g.db.hget('config', 'client_id'),
              'client_secret': g.db.hget('config', 'client_secret')}
    r = requests.get(API_ROOT + '/auth/token', params=params)
    print r.text
    token_json = r.json()
    params = {'session': token_json['access_token']}
    r = requests.get(API_ROOT + '/user/detail', params=params)
    print r.text
    user_id = r.json().get("userid")
    if user_id:
        g.db.hset("user_token", user_id, json.dumps(token_json))
        c_uuid = uuid.uuid4()
        resp = make_response(redirect(url_for('index')))
        g.db.set("c_uuid_" + c_uuid, user_id, ex=2592000)
        resp.set_cookie("c_uuid", c_uuid)
        return resp
    return jsonify(r.text)


@application.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if g.db.hexists('config', 'client_id') and g.db.hexists('config', 'client_secret'):
        user_id = None
        c_uuid = request.cookies.get("c_uuid")
        if c_uuid:
            user_id = g.db.get("c_uuid_" + c_uuid)
        print user_id, c_uuid
        if not user_id:
            query = [("redirect_uri", url_for('auth', _external=True)),
                     ("response_type", "code"),
                     ("client_id", g.db.hget('config', 'client_id'))]
            return redirect(API_ROOT + '/auth/auth?' + urllib.urlencode(query))
        if request.method == 'POST':
            g.db.hset('user_maker_key', user_id, request.form['maker_key'])
        maker_key = g.db.hget('user_maker_key', user_id)
        return render_template("index.html", error=error, user_id=user_id, maker_key=maker_key)
    else:
        return redirect(url_for('config'))


@application.route('/config', methods=['GET', 'POST'])
def config():
    error = None
    if request.method == 'POST':
        g.db.hsetnx("config", "client_id", request.form['client_id'])
        g.db.hsetnx("config", "client_secret", request.form['client_secret'])
        return redirect(url_for('index'))
    else:
        return render_template('config.html', error=error)


if __name__ == '__main__':
    application.debug = True
    application.run()
