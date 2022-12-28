import pandas as pd
import nltk
import sqlite3
import emoji

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

SKIN_TONE_SUFFIXES = [
    'medium-light_skin_tone',
    'light_skin_tone',
    'medium_skin_tone',
    'medium-dark_skin_tone',
    'dark_skin_tone',
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

    def filter_list(self, list1):
        return sorted(
            list(set(list1).intersection(self.emoji_df['label'].tolist())))

    def add_variants(self, base_label):

        base_search = base_label[1:-1]
        if base_search in SKIN_TONE_SUFFIXES:
            return []
        variants = [f":{base_search}_{x}:" for x in SKIN_TONE_SUFFIXES]
        man_variants = [':man_' + base[1:]
                        for base in variants] + [f':man_{base_search}:']
        woman_variants = [':woman_' + base[1:]
                          for base in variants] + [f':woman_{base_search}:']
        return self.filter_list(variants) + self.filter_list(
            woman_variants) + self.filter_list(man_variants)

    def top_emojis(self, search):
        search = self.w.lemmatize(search.strip().lower())
        if (idx := self.vocab_dict.get(search)):
            return self.emoji_df.iloc[(
                self.distances[idx])].query('version <= 14.0')
        else:
            return pd.DataFrame(columns=['text', 'emoji'])


class EmojiFinderSql(EmojiFinderCached):

    def __init__(self, model_name='all-mpnet-base-v2'):
        print('Begin init of class')
        #self.con = sqlite3.connect(
        #    'main.db')  #change later, name should have model type in it
        self.w = nltk.WordNetLemmatizer()
        self.all_labels = pd.read_sql('select distinct label from emoji;',
                                      con=self.con)['label'].tolist()
        self.base_emoji_map = self.make_variant_map()
        self.make_variant_map()
        self.emoji_dict = pd.read_sql(
            "select * from emoji;",
            con=self.con).set_index('label')[['emoji', 'text']].to_dict(
                'index')  # would love to avoid this?
        _ = self.w.lemmatize('test')
        print('end init of class')

    @property
    def con(self):
        return sqlite3.connect('main.db')

    def make_variant_map(self):
        no_variants = pd.read_sql('select distinct word from lookup_emoji;',
                                  con=self.con)['word'].tolist()
        new_dict = {}
        for non_variant in no_variants:
            the_variants = self.add_variants(non_variant)
            new_dict.update({var: non_variant for var in the_variants})
        return new_dict

    def filter_list(self, list1):
        return sorted(list(set(list1).intersection(self.all_labels)))

    def top_emojis(self, search):
        if not emoji.is_emoji(search):
            search = self.w.lemmatize(search.strip().lower())
            results = pd.read_sql(
                "select  emoji,rank_of_search,label,text,version from combined where word = (?) order by rank_of_search;",
                con=self.con,
                params=(search, ))
        else:
            search = emoji.demojize(search)
            if base_emoji := self.base_emoji_map.get(search):
                search = base_emoji
            results = pd.read_sql(
                "select  emoji,rank_of_search,label,text,version from combined_emoji where word = (?) order by rank_of_search;",
                con=self.con,
                params=(search, ))
        if not results.empty:
            return results.query(
                'version <= 14.0')  ## move this into sql and add index?
        else:
            return pd.DataFrame(columns=['text', 'emoji'])
