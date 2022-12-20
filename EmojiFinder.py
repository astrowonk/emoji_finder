import pandas as pd
import nltk

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# class EmojiFinder():

#     def __init__(self):
#         self.emoji_df = pd.read_parquet('emoji_data.parquet')
#         self.score_array = pd.read_parquet('emoji_scores.parquet').values
#         self.model = SentenceTransformer('all-mpnet-base-v2')

#     def top_emojis(self, search):
#         search = w.lemmatize(search)
#         target = self.model.encode(search)
#         tensor = util.cos_sim(target, self.score_array)
#         locs = (-tensor.numpy()).argsort()[0][0:20]
#         return self.emoji_df.iloc[locs]


class EmojiFinderCached():

    def __init__(self, model_name='all-mpnet-base-v2'):
        self.emoji_df = pd.read_parquet('emoji_data.parquet')
        self.emoji_dict = self.emoji_df.set_index('label')['emoji'].to_dict()
        self.emoji_text_dict = self.emoji_df.set_index(
            'label')['text'].to_dict()

        vocab_df = pd.read_parquet(f'vocab_df_{model_name}.parquet')
        self.vocab_dict = vocab_df.set_index('word')['idx'].to_dict()
        self.distances = pd.read_parquet(
            f'semantic_distances_{model_name}.parquet').values
        self.w = nltk.WordNetLemmatizer()

    def top_emojis(self, search):
        search = self.w.lemmatize(search.strip().lower())
        if (idx := self.vocab_dict.get(search)):
            return self.emoji_df.iloc[(self.distances[idx])]
        else:
            return pd.DataFrame(columns=['text', 'emoji'])
