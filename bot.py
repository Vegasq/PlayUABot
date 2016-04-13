#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Post fresh PlayUA entries to Telegram
# Mykola Yakovliev <vegasq@gmail.com>
# 2016

import telegram
import feedparser
import pickledb
from telegram.ext import Updater
from telegram.error import NetworkError, Unauthorized

import time
from time import sleep
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class PlayUABot(object):
    _key = open('/etc/playua.cfg', 'r').read().replace('\n', '')
    _rss_url = "http://playua.net/feed/"
    _db_path = "/playuadb/playua.db"

    def __init__(self):
        logging.debug('Starting application...')
        self._db = pickledb.load(self._db_path, False)
        self._bot = telegram.Bot(self._key)
        self._last_rss_call = None
        self._entries = []

        # self.dispatch()

    @staticmethod
    def help(bot, update):
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Маленький чатбот який повідомлює про новини "
                             "на сайті PlayUA.net")

    def dispatch(self):
        self._updater = Updater(token=self._key)
        self._updater.dispatcher.addTelegramCommandHandler('help', self.help)
        logging.error('start poll')
        self._updater.start_polling()
        logging.error('stop poll')

    @property
    def chats(self):
        chats = set()
        for update in self._bot.getUpdates(timeout=1):
            chats.add(update.message.chat_id)
        return chats

    @property
    def rss(self):
        if not self._last_rss_call or time.time() - self._last_rss_call > 10:
            self._last_rss_call = time.time()

            logging.debug('Get feed from PlayUA')
            d = feedparser.parse(self._rss_url)

            self._entries = []
            for entry in d['entries']:
                entry_in_db = self._db.get(entry['id'])
                if not entry_in_db:
                    self._db.set(entry['id'], 'True')
                    self._entries.append(entry)
            logging.debug('Save DB')
            self._db.dump()
            return self._entries
        else:
            return self._entries

    def format_message(self, entry):
        return """{title}\n{link}""".format(**entry)

    def start(self):
        while True:
            try:
                logging.debug("Chats:")
                logging.debug(self.chats)
                for entry in self.rss:
                    for chat_id in self.chats:
                        self._bot.sendMessage(
                            chat_id=chat_id,
                            text=self.format_message(entry))
            except NetworkError:
                logging.error('NetworkError')
                sleep(1)
                raise
            except Unauthorized:
                logging.error('Unauthorized')
                sleep(1)


if __name__ == '__main__':
    PlayUABot().start()
