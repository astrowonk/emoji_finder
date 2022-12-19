import streamlit as st
from EmojiFinder import EmojiFinderCached

st.set_page_config(page_title="Emoji Finder", )

st.title('Semantic Emoji Search')


@st.experimental_memo(ttl=3600)
def make_class():

    return EmojiFinderCached()


e = make_class()

search = st.text_input("Search")
col1, col2 = st.columns(2)

if search:
    st.subheader("Results:")
    for item in e.top_emojis(search)[['text', 'emoji']].to_dict('records'):
        st.markdown(item['text'])
        st.code(item['emoji'])
