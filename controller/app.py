#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 网站应用类
@time: 2018/10/23
"""

import re
import os
import shutil
import pymongo
from os import path
from yaml import load as load_yml, SafeLoader
from operator import itemgetter
from tornado import web
from tornado.options import define, options
from tornado.util import PY3
from tornado.log import access_log
from controller.role import url_placeholder


__version__ = '0.1.0.90710'
BASE_DIR = path.dirname(path.dirname(__file__))

define('testing', default=False, help='the testing mode', type=bool)
define('debug', default=True, help='the debug mode', type=bool)
define('port', default=8000, help='run port', type=int)


class Application(web.Application):
    def __init__(self, handlers, **settings):
        def create_dir(path_name):
            if not path.exists(path_name):
                try:
                    os.mkdir(path_name)
                except OSError:
                    pass

        self._db = self.config = self.site = None
        self.load_config(settings.get('db_name_ext'))

        self.IMAGE_PATH = path.join(BASE_DIR, 'static', 'img')
        create_dir(self.IMAGE_PATH)

        self.version = __version__
        self.BASE_DIR = BASE_DIR
        self.handlers = handlers
        handlers = [(r'/upload/(\w+/\w+\.(png|jpg|jpeg|gif|bmp))', web.StaticFileHandler,
                     dict(path=path.join(BASE_DIR, 'static', 'upload')))]
        create_dir(path.join(BASE_DIR, 'static', 'upload'))

        for cls in self.handlers:
            if isinstance(cls.URL, list):
                handlers.extend((self.url_replace(url), cls) for url in cls.URL)
            else:
                handlers.append((self.url_replace(cls.URL), cls))

        handlers = sorted(handlers, key=itemgetter(0))
        web.Application.__init__(
            self, handlers, debug=options.debug, login_url='/user/login', compiled_template_cache=False,
            static_path=path.join(BASE_DIR, 'static'),
            template_path=path.join(BASE_DIR, 'views'),
            cookie_secret=self.config['cookie_secret'],
            log_function=self.log_function,
            **settings
        )

    @staticmethod
    def url_replace(url):
        for k, v in url_placeholder.items():
            url = url.replace('@' + k, '(%s)' % v)
        return url

    def log_function(self, handler):
        summary = handler._request_summary()
        s = handler.get_status()
        if not (s in [304, 200] and re.search(r'GET /(static|api/(pull|message|discuss))', summary) or s == 404):
            nick = hasattr(handler, 'current_user') and handler.current_user
            nickname = nick and (hasattr(nick, 'name') and nick.name or nick.get('name')) or ''
            request_time = 1000.0 * handler.request.request_time()
            log_method = access_log.info if s < 400 else access_log.warning if s < 500 else access_log.error
            log_method("%d %s %.2fms%s", s, summary, request_time, nickname and ' [%s]' % nickname or '')

    @property
    def db(self):
        if not self._db:
            cfg = self.config['database']
            uri = cfg['host']
            if cfg.get('user'):
                uri = 'mongodb://{0}:{1}@{2}:{3}/admin'.format(
                    cfg.get('user'), cfg.get('password'), cfg.get('host'), cfg.get('port', 27017)
                )
            conn = pymongo.MongoClient(
                uri, connectTimeoutMS=2000, serverSelectionTimeoutMS=2000, maxPoolSize=10, waitQueueTimeoutMS=5000
            )
            self._db = conn[cfg['name']]
        return self._db

    def load_config(self, db_name_ext=None):
        param = dict(encoding='utf-8') if PY3 else {}
        cfg_file = path.join(BASE_DIR, 'app.yml')
        if not os.path.exists(cfg_file):
            shutil.copy(path.join(BASE_DIR, '_app.yml'), cfg_file)
        with open(cfg_file, **param) as f:
            self.config = load_yml(f, Loader=SafeLoader)
            self.site = self.config['site']
            self.img = self.config['img']
            self.site['url'] = 'localhost:{0}'.format(options.port)
            if db_name_ext and not self.config['database']['name'].endswith('_test'):
                self.config['database']['name'] += db_name_ext

    def stop(self):
        pass
