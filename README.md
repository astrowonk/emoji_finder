
## Semantic Emoji Search

**[Try the Live Web App](http://marcoshuerta.com/dash/emoji_finder/)**

Inspired (nerd sniped?) by [this post](https://data-folks.masto.host/@archie/109543055657581394) on Mastodon, I have created this effort to do semantic searching for emoji. So, you can search for `flower`, and also get `bouquet` 💐, and `cherry blossom` 🌸. (The iOS emoji keyboard does something similar, but this remains unavailable on MacOS.)

I'm using the python `sentence_tranformers` [package available from SBERT](https://www.sbert.net/index.html). This has a variety of [pretrained models suitable](https://www.sbert.net/docs/pretrained_models.htm) for the task of finding a semantic match between a search term and a target.

In order to get this to run in the low memory environment of [streamlit](https://share.streamlit.io), or on my [own web site under dash](http://marcoshuerta.com/dash/emoji_finder/), I made a version that uses *precomputed semantic distance* against a corpus of common english words. This has the benefit of running with low memory on the web without pytorch, but the search only works for one-word searches. I may try to add command two-word phrases, but I imagine that data set would get large fast.

The `EmojiFinder` class in `EmojiFinderPytorch.py` live encodes the search term, but still has a pre-encoded vectors for the emojis. 

### Dash App Screen recording




https://user-images.githubusercontent.com/13702392/209137437-4014ab8f-ceac-4528-a73d-38147d9f32b4.mp4



TODO:

* Make a config file so one can run it with the full pytorch-requiring library (which can handle longer search terms)
* Add other preferences like filtering max emoji version, and emoji font size. (Currently hardcoded to 14 or lower.)
* Enhance the encoded text for emoji? A person with a laptop is called a "technologist"; if that had a better description, the search would be better at finding it. I'd need some alternate description info, however, not in the [python emoji library](https://pypi.org/project/emoji/)
* Actually use Github issues and not this markdown list.
~~* Add persistent preferences for surfacing prioritizing which genders and skin tones to put at top of search.~~
* ~~Make a Dash version for more layout flexibility / persistent preferences. (Maybe)~~
  * ~~Alternative : Figure out persistent preferences in Streamlit~~. 
* ~~Group different gender and skin tone variants of the same emoji on the same line. (i.e. include with the top result e.g. :supervillain:)~~
* ~~Add the scripts that build the pre-computed distances.~~
* ~~Compute distances with other methods (dot product) and models (pre-computed distances currently using only `all-mpnet-base-v2`)~~
