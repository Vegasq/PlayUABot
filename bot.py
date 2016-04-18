#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Post fresh PlayUA entries to Telegram
# Mykola Yakovliev <vegasq@gmail.com>
# 2016

import telegram
import feedparser
from telegram.error import NetworkError, Unauthorized

import time
from time import sleep
import logging
import json

import db


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


with open('config.json', 'r', encoding='utf-8') as fl:
    config = json.loads(fl.read())


class NoChatsFound(Exception):
    pass


class get_chats(object):
    def __init__(self, chat_manager):
        self.chat_manager = chat_manager

    def __enter__(self):
        self.chat_manager.refresh()
        if len(self.chat_manager.chats) == 0:
            raise NoChatsFound()
        return self.chat_manager.chats

    def __exit__(self, type, value, traceback):
        pass


class get_entries(object):
    def __init__(self, feed_managers):
        self.feed_managers = feed_managers

    def __enter__(self):
        entries = []
        for fm in self.feed_managers:
            fm.refresh()
            entries += fm.entries
        return entries

    def __exit__(self, type, value, traceback):
        for fm in self.feed_managers:
            fm.clear()


class Feed(object):
    def __init__(self, context, url):
        self.context = context
        self.url = url
        self.entries = []

        self._last_refresh = None

    def clear(self):
        self.entries = []

    def refresh(self):
        logging.debug("Refresh feed")
        if not self._last_refresh or time.time() - self._last_refresh > 10:
            self._last_refresh = time.time()

            logging.debug('Get feed from PlayUA')
            d = feedparser.parse(self.url)

            self.entries = []
            logging.debug(d['entries'])
            for entry in d['entries']:
                entry_in_db = db.db_get(entry['id'])

                if not entry_in_db:
                    logging.debug('Post %s not found in DB' % entry['id'])
                    db.db_set(entry['id'])
                    self.entries.append(entry)
            logging.debug("Refresh feed done")


class Chat(object):
    def __init__(self, context, chat):
        self._chat = chat
        self.context = context

    def _format_message(self, entry):
        return """<a href=\"{link}\">{title}</a>""".format(**entry)

    def send(self, message):
        logging.debug("Send message to chat %s: %s" % (self, message))
        self.context.bot.sendMessage(chat_id=self._chat.id,
                                     text=self._format_message(message),
                                     parse_mode=telegram.ParseMode.HTML)


class Chats(object):
    def __init__(self, context):
        self.context = context
        self._chats = {}

    def _add(self, chat):
        if chat.id not in self._chats.keys():
            self._chats[chat.id] = Chat(self.context, chat)

    def refresh(self):
        logging.debug("Refresh chats")
        try:
            for update in self.context.bot.getUpdates(timeout=10):
                self._add(update.message.chat)
        except NetworkError as e:
            logging.error(e)

    @property
    def chats(self):
        return self._chats.values()


class PlayUABot(object):
    _key = config['secret_key']
    _rss_urls = config['feeds']

    def __init__(self):
        logging.debug('Starting application...')
        self.debug = False

        self.bot = telegram.Bot(self._key)

        self.chats_manager = Chats(self)

        self.feed_managers = []
        for url in self._rss_urls:
            feed_manager = Feed(self, url)
            self.feed_managers.append(feed_manager)

    def start(self):
        logging.debug('Main loop started')
        while True:
            logging.debug('Main loop iteration')
            try:
                # Trick in next few lines, chats should be locked first,
                # cause in ase of error new entries from feeds wount be
                # marked as readed.
                with get_chats(self.chats_manager) as chats, \
                     get_entries(self.feed_managers) as entries:

                    logging.debug("Send to %s chats %s messages." % (
                        len(chats), len(entries)))

                    for chat in chats:
                        for entry in entries:
                            logging.debug(
                                "Send msg to chat %s: %s" % (chat, entry))

                            if not self.debug:
                                chat.send(entry)
            except NoChatsFound:
                logging.error('NoChatsFound')
                sleep(1)
            except NetworkError:
                logging.error('NetworkError')
                sleep(1)
            except Unauthorized:
                logging.error('Unauthorized')
                sleep(1)


if __name__ == '__main__':
    PlayUABot().start()
