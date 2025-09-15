import duckdb
import llama_cpp
from functools import cache


class LiveSearch:
    def __init__(self, model_path) -> None:
        self.model = llama_cpp.Llama(model_path=model_path, embedding=True, verbose=False)

        self.con = duckdb.connect('vectors.db', read_only=True)
        self.get_emoji = cache(self._get_emoji)

    def _get_emoji(self, search):
        search_vector = self.model.embed(search)

        return self.con.sql(
            """select id, array_cosine_similarity(arr,?::DOUBLE[384]) as similarity,
	e.* from array_table a left join emoji_df e on
	a.id = e.idx where label = base_emoji 
    order by similarity desc limit 25;""",
            params=(search_vector,),
        ).to_df()
