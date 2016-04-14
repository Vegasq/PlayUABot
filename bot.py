#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Post fresh PlayUA entries to Telegram
# Mykola Yakovliev <vegasq@gmail.com>
# 2016

import telegram
import feedparser
import pickledb
# from telegram.ext import Updater
from telegram.error import NetworkError, Unauthorized

import time
from time import sleep
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Feed(object):
    def __init__(self, context, url):
        self.context = context
        self.url = url
        self._last_refresh = None
        self.entries = []
        self.skip_exists = False

        self._db = pickledb.load(self.context.db_path, False)

    def refresh(self):
        logging.debug("Refresh feed")
        if not self._last_refresh or time.time() - self._last_refresh > 10:
            self._last_refresh = time.time()

            logging.debug('Get feed from PlayUA')
            d = feedparser.parse(self.url)

            self.entries = []
            logging.debug(d['entries'])
            for entry in d['entries']:
                entry_in_db = self._db.get(entry['id'])
                if not entry_in_db:
                    self._db.set(entry['id'], 'True')
                    if not self.skip_exists:
                        self.entries.append(entry)
            self._db.dump()
            logging.debug("Refresh feed done")


class Chat(object):
    def __init__(self, context, chat):
        self._chat = chat
        self.context = context

    def _format_message(self, entry):
        return """<a href=\"{link}\">{title}</a>""".format(**entry)

    def send(self, message):
        logging.debug("Send message to chat %s: %s" % (self, message))
        logging.debug(message)
        # if 'media_thumbnail' in message and message['media_thumbnail']:
        #     self.context.bot.sendPhoto(
        #         chat_id=self._chat.id,
        #         photo=message['media_thumbnail'][0]['url'],
        #         disable_notification=True)

        # disable_preview = None
        # if 'media_thumbnail' in message and message['media_thumbnail']:
        #     disable_preview = True
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
            # raise

    @property
    def chats(self):
        return self._chats.values()


class PlayUABot(object):
    _key = open('/etc/playua.cfg', 'r').read().replace('\n', '')
    _rss_urls = [
        "http://playua.net/feed/",
        "https://www.youtube.com/feeds/videos.xml?"
        "channel_id=UCKJZ5id-vvCi9_5ERTmBNHQ"
    ]

    db_path = "playua.db"

    def __init__(self):
        logging.debug('Starting application...')

        self.bot = telegram.Bot(self._key)

        self.chats_manager = Chats(self)
        self.chats_manager.refresh()

        self.feed_managers = []
        for url in self._rss_urls:
            feed_manager = Feed(self, url)
            feed_manager.refresh()
            self.feed_managers.append(feed_manager)

        self.debug = False

        # self.dispatch()

    # @staticmethod
    # def help(bot, update):
    #     bot.sendMessage(chat_id=update.message.chat_id,
    #                     text="Маленький чатбот який повідомлює про новини "
    #                          "на сайті PlayUA.net")

    # def dispatch(self):
    #     self._updater = Updater(token=self._key)
    #     self._updater.dispatcher.addTelegramCommandHandler('help', self.help)
    #     logging.error('start poll')
    #     self._updater.start_polling()
    #     logging.error('stop poll')

    def start(self):
        logging.debug('Loop started')
        while True:
            try:
                logging.debug("Chats: %s" % self.chats_manager.chats)
                for chat in self.chats_manager.chats:
                    for fmgmt in self.feed_managers:
                        for entry in fmgmt.entries:
                            if self.debug:
                                logging.debug("Send fake to chat %s: %s" % (
                                    chat, entry))
                            else:
                                chat.send(entry)

            except NetworkError:
                logging.error('NetworkError')
                sleep(1)
                # raise
            except Unauthorized:
                logging.error('Unauthorized')
                sleep(1)
                # raise

            for mng in self.feed_managers + [self.chats_manager]:
                mng.refresh()
            logging.debug('Data refreshed')


if __name__ == '__main__':
    PlayUABot().start()
