#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Post fresh PlayUA entries to Telegram
# Mykola Yakovliev <vegasq@gmail.com>
# 2016

import peewee
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


db = peewee.SqliteDatabase('playua_sql.db')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Post(BaseModel):
    post_id = peewee.CharField(unique=True)


db.connect()
try:
    db.create_tables([Post])
except peewee.OperationalError:
    pass


def db_get(row_id):
    try:
        return Post.get(Post.post_id == row_id)
    except peewee.DoesNotExist:
        return None


def db_set(row_id):
    try:
        p = Post(post_id=row_id)
        p.save()
    except peewee.IntegrityError as e:
        logging.error(e)
