
## Semantic Emoji Search

**[----->  Try the Live Web App <-----](http://marcoshuerta.com/dash/emoji_finder/)**

If you're a Mac user who uses (or wants to try) LaunchBar, try my [Semantic Emoji Finder Launch Bar Action](https://github.com/astrowonk/Emoji-Semantic-Search-LaunchBar-Action).

Inspired ([nerd sniped?](https://xkcd.com/356/)) by [this post](https://data-folks.masto.host/@archie/109543055657581394) on Mastodon, I have created this effort to do semantic searching for emoji. So, you can search for `flower`, and also get `bouquet` 💐, and `cherry blossom` 🌸. (The iOS emoji keyboard does something similar, but this remains unavailable on MacOS.)

I'm using the python `sentence_tranformers` [package available from SBERT](https://www.sbert.net/index.html). This has a variety of [pretrained models suitable](https://www.sbert.net/docs/pretrained_models.htm) for the task of finding a semantic match between a search term and a target. I'm using the `all-mpnet-base-v2` model for the web apps.

The web app now functions in two ways. The first is to precompute everything and store results for one-word search queries in sqlite. This uses *precomputed semantic distance* against a corpus of common english words (now 40,000 words). The top results are stored in a database in `all-mpnet-base-v2_main.db ` along with lookup tables, indices, and views that make looking up a word a [simple sql query](https://github.com/astrowonk/emoji_finder/blob/06ddc28c9f35458dd8d4e772cb9109530e86f616/EmojiFinder.py#L127).

For longer queries, I used the `precompute.py` file to generate `all-MiniLM-L6-v2` vectors which I store in the duckdb database `vectors.db`, now that DuckDB supports [fixed size arrays](https://duckdb.org/2024/02/13/announcing-duckdb-0100.html#fixed-length-arrays). Then the `LiveSearch` class can use `llama.cpp` to create a vector for the search term (thanks to new [BERT support in llama.cpp](https://github.com/ggerganov/llama.cpp/pull/5423)) and DuckDB can find the most similar emojis using cosine similarity with a short query:

```sql
  select id,array_cosine_similarity(arr,?::DOUBLE[384]) as similarity,e.* from array_table a left join emoji_df e on a.id = e.idx where label = base_emoji order by similarity desc limit 25;"
```

The dash app also includes a 2D projection of the `sentence_transformer` vectors via [UMAP](https://umap-learn.readthedocs.io/en/latest/). This shows the emojis as they relate to each other semantically. This is limited to 750 emoji on the graph at once, but more will appear as one zooms in on the plotly graph. Clicking on an emoji will display it with a button to copy to the clipboard. 


## TODO

I'm not sure if all the code needed to recreate the databases is all actually in this repository. I went from caching the vectors in parquet to SQlite, and then added duckdb. My main todo is to clean this up so it's clear what needs to be run in `precompute.py` to generate the databases and models needed for the Dash app to run properly.


