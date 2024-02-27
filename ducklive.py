import duckdb
import llama_cpp


class DuckTest:

    def __init__(self, model_path) -> None:
        self.model = llama_cpp.Llama(model_path=model_path,
                                     embedding=True,
                                     verbose=False)

        self.con = duckdb.connect('vectors.db', read_only=True)

    def get_emoji(self, text):
        arr = self.model.create_embedding(text)['data'][0]['embedding']

        return self.con.sql(
            f"select id,array_cosine_similarity(arr,{arr}::DOUBLE[384]) as similarity,e.* from array_table a left join emoji_df e on a.id = e.idx order by similarity desc limit 20;"
        ).to_df()
