"""Pre-generate needed model scores for emoji finding clasess."""

from sentence_transformers import SentenceTransformer, util
import torch
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import duckdb
from EmojiFinder import EmojiFinderCached


class ComputeDistances:
    distance_df = None

    def __init__(
        self, model_name='all-mpnet-base-v2', emoji_prefix='', vocab_prefix='', vocab_suffix=''
    ) -> None:
        self.model_name = model_name
        self.emoji_prefix = emoji_prefix
        self.vocab_prefix = vocab_prefix
        self.vocab_suffix = vocab_suffix
        self.emoji_data = pd.read_parquet(
            'emoji_df_improved.parquet'
        )  # dataframe of emojis and their descriptions
        if (
            torch.backends.mps.is_available()
        ):  # use metal back end if available (on an Apple Silicon Mac)
            # I probably should add a similar hook  for CUDA but this is fast enough it doesn't really need CUDA
            self.model = SentenceTransformer(
                model_name, device=torch.device('mps'), trust_remote_code=True
            )
        else:
            self.model = SentenceTransformer(model_name)
        self.all_words = (
            pd.read_csv('cleaned_wordlist_allv2.txt', header=None)[0].dropna().tolist()
        )  ## this list has not been lemmatized, but de-duplicated already. Lemmatization at runtime is too memory intensive with nltk

    def make_emoji_vectors(self):
        emoji_dict = self.emoji_data.set_index('label')['text'].to_dict()
        no_variants = [x for x in self.emoji_data['label'].to_list() if 'skin_tone' not in x]
        #  no_variants = [x for x in no_variants if not (x.startswith(':woman'))]
        # no_variants = [x for x in no_variants ]
        # no_variants = no_variants + [':man:', ':woman:']
        text_list = [emoji_dict[x] for x in no_variants]
        text_list = [self.emoji_prefix + x for x in text_list]
        self.vector_array_emoji = self.model.encode(text_list)
        self.vector_array_emoji_df = pd.DataFrame(self.vector_array_emoji)
        self.vector_array_emoji_df.index = no_variants
        self.vector_array_emoji_df.columns = [
            str(x) for x in self.vector_array_emoji_df.columns
        ]  ## parquet needs string columns
        map_index_orig = {key: i for i, key in enumerate(emoji_dict.keys())}
        map_index_limited = {i: key for i, key in enumerate(no_variants)}
        self.map_index_limited = map_index_limited
        self.index_to_index = {
            i: map_index_orig[map_index_limited[i]] for i in range(len(no_variants))
        }

    def make_vocab_vectors(self, n=40000):
        vocab = self.all_words[:n]
        self.vector_array_search_terms = self.model.encode(
            [self.vocab_prefix + x + self.vocab_suffix for x in vocab]
        )
        self.vocab_df = pd.DataFrame(pd.Series(vocab)).reset_index()
        self.vocab_df.columns = ['idx', 'word']

    def make_all(self):
        print('making emoji vectors')
        self.make_emoji_vectors()
        print('making vocab dataframe')
        self.make_vocab_vectors()
        print('computing distances')
        self.precompute_distances()

    def precompute_distances(self, method='cos', n=25):
        if method != 'cos':
            distances = util.dot_score(
                self.vector_array_search_terms, self.vector_array_emoji
            ).numpy()
        else:
            distances = util.cos_sim(
                self.vector_array_search_terms, self.vector_array_emoji
            ).numpy()

        self.raw_distances = distances

        top_n = np.argsort(-distances)[:, 0:n]
        self.distance_df = pd.DataFrame(top_n)
        self.distance_df.columns = [str(x) for x in self.distance_df.columns]

    def save_all(self):
        self.distance_df.to_parquet(
            f'semantic_distances_{self.model_name.replace("/","-")}.parquet'
        )  # precomputed top 25 indices of matching emojis
        self.vocab_df.to_parquet(
            f'vocab_df_{self.model_name.replace("/","-")}.parquet'
        )  # matches indices to the emoji itself (could combine into a single lookup dict)
        self.vector_array_emoji_df.to_parquet(
            f'emoji_vectors_{self.model_name.replace("/","-")}.parquet'
        )  ## needed to speed up live encoding
        ## of the search terms, only need to model.encode(search).

    def save_emoji_vectors_only(self):
        self.distance_df.to_parquet(
            f'semantic_distances_{self.model_name.replace("/","-")}.parquet'
        )
        self.distance_df.to_parquet(f'vocab_df_{self.model_name.replace("/","-")}.parquet')

    def make_database(self, db_name=None):
        """Need to test this!"""
        if not db_name:
            db_name = f'{self.model_name.replace("/","-")}_main.db'
        con = create_engine(f'sqlite:///{db_name}')
        self.distance_df.index = self.vocab_df['word']
        new_df = self.distance_df.T
        new_df.index.name = 'rank_of_search'
        melted_df = pd.melt(
            new_df.reset_index(), value_name='word_lookup', id_vars=['rank_of_search']
        )
        melted_df['word_lookup'] = melted_df['word_lookup'].map(self.index_to_index)
        melted_df['rank_of_search'] = melted_df['rank_of_search'].astype(int)
        melted_df.to_sql('lookup', con=con, index=False, if_exists='replace')
        self.emoji_data.reset_index().rename(columns={'index': 'idx'}).to_sql(
            'emoji_df', con=con, index=False, if_exists='replace'
        )


def make_duckb_vectors(model_name):
    c = ComputeDistances(model_name)
    c.make_emoji_vectors()
    array_list = c.vector_array_emoji_df.values.tolist()
    con = duckdb.connect('vectors.db')
    con.sql('CREATE or replace TABLE array_table (id INT, arr double[384])')
    for i in range(len(array_list)):
        sql = f'insert into array_table values({c.index_to_index[i]},{array_list[i]});'
        con.sql(sql)
    con.sql('create index array_id on array_table(id);')
    con.commit()
    con.close()


def make_variant_map(no_variants, all_labels):
    print(len(no_variants))
    new_dict = {}
    for non_variant in no_variants:
        the_variants = EmojiFinderCached.add_variants(non_variant, all_labels)
        new_dict.update({var: non_variant for var in the_variants})
    return new_dict


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('model_name')

    args = parser.parse_args()

    c = ComputeDistances(args.model_name)
    c.make_all()
    c.make_database()
    make_duckb_vectors('all-MiniLM-L6-v2')
