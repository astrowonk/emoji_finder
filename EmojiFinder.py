import pandas as pd
import sqlite3
import emoji

SKIN_TONE_SUFFIXES = [
    'medium-light_skin_tone',
    'light_skin_tone',
    'medium_skin_tone',
    'medium-dark_skin_tone',
    'dark_skin_tone',
]


def flatten_list(list_of_lists):
    return [y for x in list_of_lists for y in x]


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

    def filter_list(self, list1):
        return sorted(
            list(set(list1).intersection(self.emoji_df['label'].tolist())))

    def add_variants(self, base_label):
        #print(base_label)
        base_search = base_label[1:-1]
        if base_search in SKIN_TONE_SUFFIXES:
            return []
        for prefix in ['person_', 'man_', 'woman_']:
            if base_search.startswith(prefix):
                base_search = base_search.replace(prefix, '')
                # print(f'new base {base_search}')
                break
        variants = [f":{base_search}_{x}:" for x in SKIN_TONE_SUFFIXES]
        #print(variants)
        man_variants = [':man_' + base[1:]
                        for base in variants] + [f':man_{base_search}:']
        woman_variants = [':woman_' + base[1:]
                          for base in variants] + [f':woman_{base_search}:']
        person_variants = [':person_' + base[1:]
                           for base in variants] + [f':person_{base_search}:']

        extra_suffixes = flatten_list(
            [[f":{gender}_{x}_{base_search}:" for x in SKIN_TONE_SUFFIXES]
             for gender in ['man', 'woman', 'person']])

        return self.filter_list(variants) + self.filter_list(
            woman_variants) + self.filter_list(
                man_variants) + self.filter_list(
                    person_variants) + self.filter_list(extra_suffixes)

    def top_emojis(self, search):
        search = search.strip().lower()
        if (idx := self.vocab_dict.get(search)):
            return self.emoji_df.iloc[(
                self.distances[idx])].query('version <= 14.0')
        else:
            return pd.DataFrame(columns=['text', 'emoji'])


class EmojiFinderSql(EmojiFinderCached):

    def __init__(self, model_name='all-mpnet-base-v2', db_name='main.db'):
        self.db_name = db_name
        print('Begin init of class')
        #self.con = sqlite3.connect(
        #    'main.db')  #change later, name should have model type in it

        self.base_emoji_map = self.make_variant_map()

        print('end init of class')

    def sql_frame(self, query, params=None):
        with sqlite3.connect(self.db_name) as con:
            return pd.read_sql(query, con=con, params=params)

    def new_emoji_dict(self, label):
        df = self.sql_frame("select * from emoji_df where label =?",
                            params=(label, ))
        return df.set_index('idx').to_dict(orient='index')[0]

    @property
    def con(self):
        return sqlite3.connect(self.db_name)

    def filter_list(self, list1):
        query_list = [f"'{x}'" for x in set(list1)]
        query_string = ",".join(query_list)
        return sorted((self.sql_frame(
            f"select label from emoji_df where label in ({query_string})")
                       ['label'].to_list()))

    def make_variant_map(self):
        no_variants = pd.read_sql('select distinct word from lookup;',
                                  con=self.con)['word'].tolist()
        new_dict = {}
        for non_variant in no_variants:
            the_variants = self.add_variants(non_variant)
            new_dict.update({var: non_variant for var in the_variants})
        return new_dict

    def top_emojis(self, search):
        print('top emoji func=')
        if not emoji.is_emoji(search):
            search = search.strip().lower()
            results = pd.read_sql(
                "select  emoji,rank_of_search,label,text,version from combined_emoji where word = ? order by rank_of_search;",
                con=self.con,
                params=(search, ))
        else:
            ##TODO we need to put the variant mapping into the main emoji_df table
            search = emoji.demojize(search)
            if base_emoji := self.base_emoji_map.get(search):
                search = base_emoji
            results = pd.read_sql(
                "select  emoji,rank_of_search,label,text,version from combined_emoji where word = ? order by rank_of_search;",
                con=self.con,
                params=(search, ))
        if not results.empty:
            return results.query(
                'version <= 14.0')  ## move this into sql and add index?
        else:
            return pd.DataFrame(columns=['text', 'emoji'])
