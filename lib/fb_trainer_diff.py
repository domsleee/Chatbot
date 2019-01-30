from chatterbot.trainers import Trainer
from chatterbot.conversation import Statement
from chatterbot import utils

class FbTrainer(Trainer):
    """
    Allows a chat bot to be trained using a message.json.
    Will learn to speak like the owner if `learn_self` is true.
    """

    def train(self, data, mimic_name):
        """
        Train the chat bot based on the provided list of
        statements that represents a single conversation.
        """

        if not 'participants' in data:
            return
        m = self._merge_messages(data)
        print('Total messages: ' + str(len(m)))

        def clean(txt):
            return txt.lower().replace('\'', '')

        statements = []
        for i in range(1, len(m)):
            if self.show_training_progress:
                utils.print_progress_bar('Fb Trainer', i+1, len(m))

            if m[i]['sender_name'] == mimic_name:
                text = clean(m[i]['content'])[:75]
                prev_text = clean(m[i-1]['content'])[-75:]
                if len(text) == 0 or len(prev_text) == 0:
                    continue
                
                search_text = self.chatbot.storage.tagger.get_bigram_pair_string(text)
                prev_search_text = self.chatbot.storage.tagger.get_bigram_pair_string(prev_text)
                #print(prev_text + ' ==> ' + text)

                statement = Statement(
                    text=text,
                    search_text=search_text,
                    in_response_to=prev_text,
                    search_in_response_to=prev_search_text,
                    conversation='training'
                )
                #print("statement from %s with response from %s" % (m[i-1]['sender_name'], m[i]['sender_name']))
                statements.append(statement)
        if len(statements):
            self.chatbot.storage.create_many(statements)
    
    def _merge_messages(self, data):
        x = []
        last_sender_name = None
        data['messages'] = sorted(data['messages'], key=lambda x: int(x['timestamp_ms']))
        for m in data['messages']:
            if 'content' in m and 'sender_name' in m:
                sender_name, content = m['sender_name'], m['content']
                content = content.encode('ascii', 'ignore').decode('ascii')
                if sender_name == last_sender_name:
                    if content.strip() != '':
                        x[len(x)-1]['content'] += '. ' + content
                else:
                    x.append({'sender_name': sender_name, 'timestamp': int(m['timestamp_ms']), 'content': content})
                last_sender_name = sender_name
        self._check_messages(x)
        return x

    def _check_messages(self, m):
        for i in range(1, len(m)):
            assert m[i]['sender_name'] != m[i-1]['sender_name']
