#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
import json
from pymongo import MongoClient
from lib.fb_trainer import FbTrainer
import os
import argparse

# Uncomment the following lines to enable verbose logging
#import logging
#logging.basicConfig(level=logging.INFO)

MESSAGES_FOLDER = '/Users/dom/Downloads/messages/'
HOST = 'localhost'
PORT = 27017
mongo = MongoClient(HOST, PORT)

# Create a new instance of a ChatBot
def main(args):
    clear_db()

    bot = ChatBot(
        'chatterbot',
        storage_adapter='chatterbot.storage.MongoDatabaseAdapter',
        database_uri='mongodb://localhost:27017/chatterbot-database',
        logic_adapters=[
            "chatterbot.logic.BestMatch"
        ]
    )
    
    x = input('Require training? (y/n): ')
    if x == 'y':
        bot.set_trainer(ChatterBotCorpusTrainer)
        bot.train('chatterbot.corpus.english')
        if args.specific:
            user = get_user()
            train_user(bot, user)
        else:
            train_all(bot)
    while True:
        try:
            req = input('User: ')
            print('Bot:', bot.get_response(req))
        except KeyboardInterrupt:
            print('Exiting..')
            break
        except Exception:
            raise

def get_user():
    files = os.listdir(MESSAGES_FOLDER)
    files = sorted(files, key=lambda s: s.lower())
    val = -1
    while val < 0 or val >= len(files):
        for i in range(len(files)):
            print(str(i)+': '+files[i])
        x = input('select user: ')
        try:
            val = int(x)
        except Exception:
            val = -1
    return files[val]

def train_all(bot):
    files = os.listdir(MESSAGES_FOLDER)
    for i in range(len(files)):
        print('train: %d/%d (%s)' % (i, len(files), files[i]))
        train_user(bot, files[i])

def train_user(bot, user):
    bot.set_trainer(FbTrainer)
    data = get_msgs(user)
    bot.train(data)

def clear_db():
    x = input('Clear database? (y/n): ')
    if x == 'y':
        db_name = 'chatterbot-database'
        print('cleared database', db_name+'.')
        mongo.drop_database(db_name)

def get_msgs(user):
    if os.path.isfile(MESSAGES_FOLDER+user+'/message.json'):
        with open(MESSAGES_FOLDER+user+'/message.json', encoding='utf-8') as f:
            return json.load(f)
    else:
        print('warning: file doesn\'t exist')
        return {}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='"intelligent" bot')
    parser.add_argument('--specific', dest='specific', action='store_true', help='train a specific folder')
    parser.add_argument('--yes', dest='feature', action='store_true', help='yes to all')
    main(parser.parse_args())
