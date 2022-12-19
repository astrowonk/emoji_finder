import pandas as pd
import nltk

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

w = nltk.WordNetLemmatizer()

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

    def __init__(self):
        self.emoji_df = pd.read_parquet('emoji_data.parquet')
        self.vocab_df = pd.read_parquet('vocab_df.parquet')
        self.distances = pd.read_parquet(
            'semantic_distances_top25.parquet').values

    def top_emojis(self, search):
        df = self.vocab_df.query('word == @search')
        if not df.empty:
            idx = df['idx'].iloc[0]
            return self.emoji_df.iloc[(self.distances[idx])]
        else:
            return pd.DataFrame(columns=['text', 'emoji'])
