"""Pre-generate needed model scores for emoji finding clasess."""

from sentence_transformers import SentenceTransformer, util
import pandas as pd
import numpy as np


class ComputeDistances:
    distance_df = None

    def __init__(self, model_name) -> None:
        self.model_name = model_name
        self.emoji_data = pd.read_parquet(
            'emoji_data.parquet')  # dataframe of emojis and their descriptions
        self.model = SentenceTransformer(model_name)
        self.all_words = pd.read_csv('cleaned_wordlist_all.txt',
                                     header=None)[0].tolist()

    def make_emoji_vectors(self):
        self.vector_array_emoji = self.model.encode(
            self.emoji_data['text']
        )  #encode the emoji text data, e.g. 'cherry blossom' or green tree
        self.vector_array_emoji_df = pd.DataFrame(self.vector_array_emoji)
        self.vector_array_emoji_df.columns = [
            str(x) for x in self.vector_array_emoji_df.columns
        ]  ## parquet needs string columns

    def make_vocab_vectors(self, n=15000):
        vocab = self.all_words[:n]
        self.vector_array_search_terms = self.model.encode(vocab)
        self.vocab_df = pd.DataFrame(pd.Series(vocab)).reset_index()
        self.vocab_df.columns = ['idx', 'word']

    def make_all(self):
        print("making emoji vectors")
        self.make_emoji_vectors()
        print("making vocab dataframe")
        self.make_vocab_vectors()
        print('computing distances')
        self.precompute_distances()

    def precompute_distances(self, method='cos', n=25):
        if method != 'cos':
            distances = util.dot_score(self.vector_array_search_terms,
                                       self.vector_array_emoji).numpy()
        else:
            distances = util.cos_sim(self.vector_array_search_terms,
                                     self.vector_array_emoji).numpy()

        top_n = np.argsort(-distances)[:, 0:n]
        self.distance_df = pd.DataFrame(top_n)
        self.distance_df.columns = [str(x) for x in self.distance_df.columns]

    def save_all(self):
        self.distance_df.to_parquet(
            f'semantic_distances_{self.model_name}.parquet'
        )  #precomputed top 25 indices of matching emojis
        self.vocab_df.to_parquet(
            f'vocab_df_{self.model_name}.parquet'
        )  # matches indices to the emoji itself (could combine into a single lookup dict)
        self.vector_array_emoji_df.to_parquet(
            f"emoji_vectors_{self.model_name}.parquet"
        )  ## needed to speed up live encoding
        ## of the search terms, only need to model.encode(search).

    def save_emoji_vectors_only(self):
        self.distance_df.to_parquet(
            f'semantic_distances_{self.model_name}.parquet')
        self.distance_df.to_parquet(f'vocab_df_{self.model_name}.parquet')


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('model_name')

    args = parser.parse_args()

    c = ComputeDistances(args.model_name)
    c.make_all()
    c.save_all()
