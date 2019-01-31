from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from chatterbot.conversation import Statement
import json
import os
from pymongo import MongoClient
from lib.fb_trainer import FbTrainer
import logging

HOST = 'localhost'
PORT = 27017
mongo = MongoClient(HOST, PORT)
DB_NAME = "chatterbot-database"

class Bot:
    def __init__(self, name, messages_folder, yes, user, db_name=DB_NAME):
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
        self._messages_folder = os.path.expanduser(messages_folder)
        if not os.path.isdir(self._messages_folder):
            raise ValueError("folder \"%s\" does not exist" % self._messages_folder)
        self._fb_trainer = FbTrainer(self._bot)
        self._yes = yes
        self._user = user

        # lazy calls
        self._get_all_files_res = False
    
    def run(self):
        if self._ask_yesno_question('Clear database? (y/n): '):
            self._clear_db()
        if self._ask_yesno_question('Require training? (y/n): '):
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

    def _ask_yesno_question(self, q):
        if self._yes:
            return True
        x = input(q)
        return x == 'y'

    def _train(self):
        self._user = self._get_user(msg='select user to mimic: ', user=self._user)
        corpus_trainer = ChatterBotCorpusTrainer(self._bot)
        corpus_trainer.train('chatterbot.corpus.english')
        files = self._get_all_files()
        for i in range(len(files)):
            file = files[i]
            print('train: %d/%d (%s)' % (i, len(files), file))
            data = self._get_msgs(file)
            self._fb_trainer.train(data, self._user)
            
    def _get_all_files(self):
        if self._get_all_files_res:
            return self._get_all_files_res

        res = []
        s = [self._messages_folder]
        while len(s):
            folder = s.pop()
            for file in os.listdir(folder):
                new_file = os.path.join(folder, file)
                if os.path.isdir(new_file):
                    s.append(new_file)
                elif file.endswith('json'):
                    res.append(new_file)

        self._get_all_files_res = res
        return res

    def _get_user(self, msg='select user: ', user=None):
        """query the cli for a user. If `user` is provided,
        throw a ValueError if `user` is invalid or return `user` if
        it is valid."""
        s = self._get_all_users()

        if user != None:
            if user in s:
                return user
            else:
                raise ValueError("User '%s' not a participant in any chat" % user)

        s = sorted(s)
        val = -1
        while val < 0 or val >= len(s):
            for i in range(len(s)):
                print(str(i)+': '+s[i])
            x = input(msg)
            try:
                val = int(x)
            except Exception:
                val = -1
        return s[val]

    def _get_all_users(self):
        """get a set of all participants"""
        files = self._get_all_files()
        s = set()
        for file in files:
            msgs = self._get_msgs(file)
            if 'participants' in msgs:
                v = {val['name'] for val in msgs['participants']}
                s = s.union(v)
        return s

    def _get_msgs(self, file):
        """get messages from a conversation"""
        path = os.path.join(file)
        if os.path.isfile(path):
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        else:
            print('warning: file "%s" doesn\'t exist' % file)
            return {}
    
    def _get_statement(self, text):
        search_text = self._bot.storage.tagger.get_bigram_pair_string(text)
        return Statement(
            text=text,
            search_text=search_text
        )

    def _clear_db(self):
        """clear database"""
        self._log.info('cleared database %s.' % self._db_name)
        mongo.drop_database(self._db_name)