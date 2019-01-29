from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from chatterbot.conversation import Statement
import json
import os
from pymongo import MongoClient
from lib.fb_trainer_diff import FbTrainer
import logging



HOST = 'localhost'
PORT = 27017
mongo = MongoClient(HOST, PORT)
DB_NAME = "chatterbot-database"

class Bot:
    def __init__(self, name, inbox_folder, only_one, db_name=DB_NAME):
        self._db_name = db_name
        self._bot = ChatBot(
            name,
            storage_adapter='chatterbot.storage.MongoDatabaseAdapter',
            database_uri='mongodb://%s:%s/%s' % (HOST, PORT, self._db_name),
            logic_adapters=[
                "chatterbot.logic.BestMatch"
            ]
        )
        self._log = logging.getLogger('Bot: '+name)
        self._name = name
        self._inbox_folder = os.path.expanduser(inbox_folder)
        self._only_one = only_one
        if not os.path.isdir(self._inbox_folder):
            raise ValueError("folder \"%s\" does not exist" % self._inbox_folder)
        self._fb_trainer = FbTrainer(self._bot)
    
    def run(self):
        self._clear_db()
        x = input('Require training? (y/n): ')
        if x == 'y':
            self._train()
        while True:
            try:
                req = self._get_statement(input('User: '))
                print('%s: %s' % (self._name, self._bot.get_response(req)))
            except KeyboardInterrupt:
                print('Exiting..')
                break
            except Exception:
                raise

    def _train(self):
        corpus_trainer = ChatterBotCorpusTrainer(self._bot)
        corpus_trainer.train('chatterbot.corpus.english')
        if self._only_one:
            user = self._get_user()
            self._train_user(user)
        else:
            self._train_all()

    def _get_user(self):
        """select a single user. Used for --only-one"""
        files = os.listdir(self._inbox_folder)
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

    def _train_all(self):
        """train using all conversations"""
        files = os.listdir(self._inbox_folder)
        for i in range(len(files)):
            print('train: %d/%d (%s)' % (i, len(files), files[i]))
            self._train_user(files[i])

    def _train_user(self, user):
        """train using a specific conversation"""
        data = self._get_msgs(user)
        self._fb_trainer.train(data)

    def _get_msgs(self, user):
        """get messages from a conversation"""
        path = os.path.join(self._inbox_folder, user, 'message.json')
        if os.path.isfile(path):
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        else:
            print('warning: file doesn\'t exist')
            return {}
    
    def _get_statement(self, text):
        search_text = self._bot.storage.tagger.get_bigram_pair_string(text)
        return Statement(
            text=text,
            search_text=search_text
        )

    def _clear_db(self):
        """ask to clear database"""
        x = input('Clear database? (y/n): ')
        if x == 'y':
            self._log.info('cleared database %s.' % self._db_name)
            mongo.drop_database(self._db_name)