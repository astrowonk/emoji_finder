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


st.markdown(
    """
    <style>
        div[data-testid="column"]:nth-of-type(1)
        {
            text-align: center;
            align-self: center;
            
        } 

        div[data-testid="column"]:nth-of-type(2)
        {
            text-align: center;
            
        } 


    </style>
    """,unsafe_allow_html=True
)


if search:
    st.subheader("Results:")
    for item in e.top_emojis(search)[['text', 'emoji']].to_dict('records'):
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.text(item['text'])
            with col2:
                st.code(item['emoji'])
        


