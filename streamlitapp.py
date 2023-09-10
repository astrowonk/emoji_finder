import streamlit as st
import streamlit.components.v1 as components
from EmojiFinder import EmojiFinderSql

st.set_page_config(page_title="Emoji Finder", )

st.title('Semantic Emoji Search')

st.markdown(
    "Also try [the Dash Version](https://marcoshuerta.com/dash/emoji_finder/) for more options and persistent settings. Source code and more info on [Github](https://github.com/astrowonk/emoji_finder)."
)


@st.cache_data(ttl=3600)
def make_class():

    return EmojiFinderSql()


e = make_class()

search = st.text_input("Search")
col1, col2 = st.columns(2)

# Auto focus on input
components.html(f"""
    <script>
        var input = window.parent.document.querySelector("input[type=text]");
        input.focus();
    </script>
    """,
                width=10,
                height=0)

st.markdown("""
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

        h1, h3 {
            padding-top: 0px;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0em;
            display: inline;
            }

        pre {
            margin-top: 1em !important;
            margin-bottom: 1em !important;
        }

        div[data-testid="stText"] {
            margin-top: 1em !important;
            margin-bottom: 1em !important;
            }


        div.block-container {
            padding: 3rem 1rem 10rem;
        }

    </style>


    """,
            unsafe_allow_html=True)

if search:
    st.subheader("Results:")

    full_res = e.top_emojis(search)
    if not full_res.empty:
        res_list = full_res.to_dict('records')
        variants = []
        for rec in res_list:
            variants.extend(e.add_variants(rec['label']))
        ## remove variants from list
        full_res = full_res.query("label not in @variants")

        for item in full_res.to_dict('records'):
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.text(item['text'])
                with col2:
                    st.code(item['emoji'])
                    additional_emojis = e.add_variants(item['label'])

                    with st.expander("See More:"):
                        for x in additional_emojis:
                            st.code(e.emoji_dict[x]['emoji'])
                            st.text(e.emoji_dict[x]['text'])
