
### Semantic Emoji Search

Inspired (nerd sniped?) by [this post](https://data-folks.masto.host/@archie/109543055657581394) on Mastodon, I have created this effort to do semantic searching for emoji. So, you can search for `flower`, and also get `bouquet` 💐, and `cherry blossom` 🌸.

I'm using the python `sentence_tranformers` [package available from SBERT](https://www.sbert.net/index.html). This has a variety of [pretrained models suitable](https://www.sbert.net/docs/pretrained_models.htm) for the task of finding a semantic match between a search term and a target.

In order to get this to run in the low memory environment of Streamlit cloud, I have version that uses precomputed semantic distance against a corpus of common english words. This has the benefit of running with low memory on the web without pytorch, but the search only works for simple one-word searches.

TODO:

* Add the scripts that build the pre-computed distances.
* Make a config file so one can run it with the full pytorch-requiring library (which can handle longer search terms)
* Compute distances with other methods (dot product) and models (pre-computed distances currently using only `all-mpnet-base-v2`)