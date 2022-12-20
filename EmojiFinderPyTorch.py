import pandas as pd
from sentence_transformers import SentenceTransformer, util
import nltk
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')


class EmojiFinder():

    def __init__(self):
        self.emoji_df = pd.read_parquet('emoji_data.parquet')
        self.score_array = pd.read_parquet('emoji_scores.parquet').values
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.w = nltk.WordNetLemmatizer()

    def top_emojis(self, search):
        search = self.w.lemmatize(search.lower().strip())
        target = self.model.encode(search)
        tensor = util.cos_sim(target, self.score_array)
        locs = (-tensor.numpy()).argsort()[0][0:20]
        return self.emoji_df.iloc[locs]
