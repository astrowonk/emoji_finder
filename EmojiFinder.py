import pandas as pd
import nltk

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

SKIN_TONE_SUFFIXES = [
    'dark_skin_tone', 'light_skin_tone', 'medium-dark_skin_tone',
    'medium-light_skin_tone', 'medium_skin_tone'
]


class EmojiFinderCached():

    def __init__(self, model_name='all-mpnet-base-v2'):
        self.emoji_df = pd.read_parquet('emoji_df_improved.parquet')
        self.emoji_dict = self.emoji_df.set_index('label')['emoji'].to_dict()
        self.emoji_text_dict = self.emoji_df.set_index(
            'label')['text'].to_dict()
        vocab_df = pd.read_parquet(f'vocab_df_{model_name}.parquet')
        self.vocab_dict = vocab_df.set_index('word')['idx'].to_dict()
        self.distances = pd.read_parquet(
            f'semantic_distances_{model_name}.parquet').values
        self.w = nltk.WordNetLemmatizer()

    def add_variants(self, base_label):
        base_search = base_label[1:-1]
        variants = [f":{base_search}_{x}:" for x in SKIN_TONE_SUFFIXES]
        man_variants = [':man_' + base[1:] for base in variants]
        woman_variants = [':woman_' + base[1:] for base in variants]

        return set(variants + man_variants + woman_variants).intersection(
            self.emoji_df['label'].tolist())

    def top_emojis(self, search):
        search = self.w.lemmatize(search.strip().lower())
        if (idx := self.vocab_dict.get(search)):
            return self.emoji_df.iloc[(self.distances[idx])]
        else:
            return pd.DataFrame(columns=['text', 'emoji'])
