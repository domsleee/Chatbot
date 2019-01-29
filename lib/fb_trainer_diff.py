from chatterbot.trainers import Trainer
from chatterbot.conversation import Statement
from chatterbot import utils

class FbTrainer(Trainer):
    """
    Allows a chat bot to be trained using a message.json.
    Will learn to speak like the owner if `learn_self` is true.
    """

    def train(self, data, learn_self=True):
        """
        Train the chat bot based on the provided list of
        statements that represents a single conversation.
        """
        def merge_messages(data):
            x = []
            last_sender_name = None
            data['messages'] = sorted(data['messages'], key=lambda x: int(x['timestamp_ms']))
            for m in data['messages']:
                if 'content' in m and 'sender_name' in m:
                    sender_name, content = m['sender_name'], m['content']
                    if sender_name == last_sender_name:
                        x[len(x)-1]['content'] += '. ' + content
                    else:
                        x.append({'sender_name': sender_name, 'content': content})
                    last_sender_name = sender_name
            return x
    
        def check_messages(m):
            for i in range(1, len(m)):
                assert m[i]['sender_name'] != m[i-1]['sender_name']

        if not 'participants' in data:
            return
        participants = data['participants']
        m = merge_messages(data)
        check_messages(m)
        print('Total messages: ' + str(len(m)))
        def clean(txt):
            return txt.lower().replace('\'', '')[-75:]

        statements = []
        for i in range(1, len(m)):
            if self.show_training_progress:
                utils.print_progress_bar('Fb Trainer', i+1, len(m))

            sn = m[i]['sender_name']
            if (learn_self and sn not in participants) or (not learn_self and sn in participants):
                text = clean(m[i]['content'])
                search_text = self.chatbot.storage.tagger.get_bigram_pair_string(text)
                prev_text = clean(m[i-1]['content'])
                prev_search_text = self.chatbot.storage.tagger.get_bigram_pair_string(prev_text)

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
