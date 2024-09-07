from dash import Output, Input, html, State, MATCH, ALL, dcc, Dash, callback_context
from dash.exceptions import PreventUpdate
import pandas as pd

import dash_bootstrap_components as dbc

from EmojiFinder import EmojiFinderSql, SKIN_TONE_SUFFIXES
from emoji import demojize, is_emoji
from ducklive import LiveSearch
from pathlib import Path

parent_dir = Path().absolute().stem

e = EmojiFinderSql(db_name='all-mpnet-base-v2_main.db')
d = LiveSearch(model_path='minilm-v6.gguf')

app = Dash(
    __name__,
    url_base_pathname=f'/dash/{parent_dir}/',
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    title='Emoji Semantic Search',
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},
    ],
)
server = app.server
STYLE = {'marginBottom': 20, 'marginTop': 20, 'width': '85%'}

range_slider = html.Div(
    [
        dbc.Label('Font Size', html_for='font-size-slider'),
        dcc.Slider(id='font-size-slider', min=1, max=4, step=0.5, value=3, persistence=True),
    ],
    className='mb-3',
)


def make_tone_options(x):
    emoji = e.new_emoji_dict(f':clapping_hands_{x}:')['emoji']
    no_punctuation = x.replace('_', ' ').replace('-', ' ')
    res = f'{emoji} {no_punctuation.title()}'
    return res


tab1_content = dbc.Container(
    children=[
        html.H3('Emoji Semantic Search', style={'text-align': 'center'}),
        html.Div(
            [
                dbc.InputGroup(
                    [
                        dbc.InputGroupText(
                            html.I(className='bi bi-search', style={'float': 'left'})
                        ),
                        dbc.Input(
                            id='search-input',
                            value='',
                            debounce=True,
                            autofocus=True,
                            placeholder='Search terms can be a word, phrase, or sentence. Or try an emoji like 🎟️.',
                        ),
                    ],
                    style=STYLE,
                ),
                dbc.Button(
                    'Settings',
                    id='expand-prefs',
                    class_name='me-1',
                    color='secondary',
                    size='sm',
                    style={'margin-top': '20px', 'margin-bottom': '20px'},
                ),
            ],
            style={
                'display': 'flex',
                'gap': '20px',
            },
        ),
        dbc.Collapse(
            [
                range_slider,
                dcc.Dropdown(
                    id='skin-tone',
                    options=[
                        {'label': make_tone_options(x), 'value': x} for x in SKIN_TONE_SUFFIXES
                    ],
                    persistence=True,
                    placeholder='Skin Tone search priority...',
                ),
                dcc.Dropdown(
                    id='gender',
                    options=['man', 'woman', 'person'],
                    persistence=True,
                    placeholder='Gender search priority...',
                ),
            ],
            id='search-priorities',
            is_open=False,
        ),
        dcc.Markdown(
            'Source code and more info on [Github](https://github.com/astrowonk/emoji_finder). Mac users may want to try the [Launchbar Action](https://github.com/astrowonk/Emoji-Semantic-Search-LaunchBar-Action).'
        ),
        html.Div(id='results'),
    ],
    style=STYLE,
)

tab2_content = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(
                id='my-graph',
                style={
                    #     'width': '120vh',
                    'height': '80vh'
                },
            )
        ),
        dbc.Col(
            html.Div(
                id='emoji-result',
                style={
                    'top': '50%',
                    'transform': 'translateY(-50%)',
                    'position': 'absolute',
                },
            ),
            width=1,
        ),
    ]
)

tab3_content = dcc.Markdown(
    """

Source code for this app and underlying modules in the [github repository](https://github.com/astrowonk/emoji_finder).

Inspired ([nerd sniped?](https://xkcd.com/356/)) by [this post](https://data-folks.masto.host/@archie/109543055657581394) on Mastodon, I made this Semantic Emoji Finder. So, you can search for `flower`, and also get `bouquet` 💐, and `cherry blossom` 🌸. (The iOS emoji keyboard does something similar, but this remains unavailable on MacOS.)

I'm using the python `sentence_tranformers` [package available from SBERT](https://www.sbert.net/index.html). This has a variety of [pretrained models suitable](https://www.sbert.net/docs/pretrained_models.htm) for the task of finding a semantic match between a search term and a target. I'm using the `all-mpnet-base-v2` model for the web apps.

In order to get this to run in a low memory environment of a web host, I *precompute semantic distance* against a corpus of common english words from [GloVe](https://nlp.stanford.edu/projects/glove/). This has the benefit of running with low memory on the web without pytorch, but the search only works for one-word searches.
                            
**February 2024 Update**: Thanks to llama.cpp and vector support in duckdb, I was able to [add multi-word search](https://github.com/astrowonk/emoji_finder/pull/7). I can now generate new embeddings with llama.cpp for a query, and use the result to query duckdb to find the most similar emojis. This runs only if the one-word pre-computed search returns no results.

The dash app also includes a 2D projection of the `sentence_transformer` vectors via [UMAP](https://umap-learn.readthedocs.io/en/latest/). This shows the emojis as they relate to each other semantically. This is limited to 750 emoji, but more will appear as one zooms in on the plotly graph. Clicking on an emoji will display it with a button to copy to the clipboard.


""",
    style=STYLE,
)

tabs = dbc.Tabs(
    [
        dbc.Tab(tab1_content, label='Search', tab_id='search-tab'),
        dbc.Tab(tab2_content, label='Graph', tab_id='graph-tab'),
        dbc.Tab(tab3_content, label='About'),
    ],
    active_tab='search-tab',
)

app.layout = dbc.Container(tabs, style=STYLE)


def wrap_emoji(record, font_size):
    return html.Div(
        [
            html.Div(
                record['emoji'],
                id=record['text'],
                style={'font-size': f'{font_size}em'},
                className='emoji',
            ),
            dcc.Clipboard(
                target_id=record['text'],
                style={
                    'margin-left': '.75em',
                    #   'padding-bottom': '1em',
                    #  'position': 'relative',
                    #                          'margin': 'auto'
                },
                className='emoji',
            ),
            dbc.Tooltip(record['label'], target=record['text']),
        ],
    )


def make_cell(item, skin_tone, gender, font_size):
    if not skin_tone:
        skin_tone = ''
    if not gender:
        gender = ''
    additional_emojis = e.sql_add_variants(item['label'])
    additional_emojis = [
        {
            'emoji': e.new_emoji_dict(x)['emoji'],
            'text': e.new_emoji_dict(x)['text'],
            'label': x,
        }
        for x in additional_emojis
    ]
    priority_result = []
    gender_result = []
    if skin_tone:
        priority_result = [x for x in additional_emojis if skin_tone in x['label']]
    if gender:
        gender_result = [
            x
            for x in priority_result or additional_emojis
            if x['label'].startswith(':' + gender)
        ]
    if gender_result:
        priority_result = gender_result

    if priority_result:
        priority_result = priority_result[0]
        additional_emojis.remove(priority_result)
        target = priority_result
    else:
        target = item
    if additional_emojis:
        return [
            html.Div(
                [
                    wrap_emoji(target, font_size),
                    dbc.Button(
                        'More',
                        id={'type': 'more-button', 'index': item['text']},
                        className='me-1',
                        size='sm',
                        outline=True,
                        color='dark',
                    ),
                ],
            ),
            dbc.Collapse(
                [wrap_emoji(item, font_size) for item in additional_emojis],
                id={'type': 'more-emojis', 'index': item['text']},
                is_open=False,
            ),
        ]
    return wrap_emoji(item, font_size=font_size)


def make_table_row(record, skin_tone, gender, font_size):
    return html.Tr(
        [
            html.Td(record['text'].title(), style={'margin': 'auto'}),
            html.Td(make_cell(record, skin_tone, gender, font_size), style={'margin': 'auto'}),
        ],
        style={'margin': 'auto'},
    )


@app.callback(
    Output('results', 'children'),
    Input('search-input', 'value'),
    Input('skin-tone', 'value'),
    Input('gender', 'value'),
    Input('font-size-slider', 'value'),
)
def search_results(search, skin_tone, gender, font_size):
    if not search:
        return html.H3('No Results')

    if len(search) > 400 or len(search.split()) > 60:
        return html.H3('Search query exceeds 400 characters or 60 words.')
    if is_emoji(search):
        search = demojize(search)
        if base_emoji := e.new_emoji_dict(search).get('text'):
            search = base_emoji
    full_res = e.top_emojis(search)
    if full_res.empty:
        print('No precomputed results. Using DuckLive')
        full_res = d.get_emoji(search)
    if full_res.empty:  # if it's still somehow empty
        return html.H3('No Results')
    full_res = full_res.drop_duplicates(subset=['label'])
    table_header = [html.Thead(html.Tr([html.Th('Description'), html.Th('Emoji')]))]
    table_rows = [
        make_table_row(rec, skin_tone, gender, font_size)
        for rec in full_res.to_dict('records')
    ]
    table_body = [html.Tbody(table_rows)]
    return dbc.Table(table_header + table_body, bordered=False, striped=True)


@app.callback(
    Output({'type': 'more-emojis', 'index': MATCH}, 'is_open'),
    State({'type': 'more-emojis', 'index': MATCH}, 'is_open'),
    Input({'type': 'more-button', 'index': MATCH}, 'n_clicks'),
)
def button_action(state, n_clicks):
    if not n_clicks:
        raise PreventUpdate
    return not state


@app.callback(
    Output('search-priorities', 'is_open'),
    State('search-priorities', 'is_open'),
    Input('expand-prefs', 'n_clicks'),
)
def button_action(state, n_clicks):
    if not n_clicks:
        raise PreventUpdate
    return not state


@app.callback(
    Output('my-graph', 'figure'),
    Input('my-graph', 'relayoutData'),
)
def make_graph(data):
    x_min, x_max = -20.0, 20.0
    y_min, y_max = -20.0, 20.0
    if data is not None and data.get('xaxis.range[0]'):
        x_min, x_max = data['xaxis.range[0]'], data['xaxis.range[1]']
        y_min, y_max = data['yaxis.range[0]'], data['yaxis.range[1]']
        print(x_min, x_max)

    df = pd.read_sql(
        f'select * from emoji_umap where  A between {x_min:.3f} and {x_max:.37} and B between {y_min:.3f} and  {y_max:.3f}  order by RANDOM() limit 600;',
        con=e.con,
    )
    fig = df.plot.scatter(
        x='A',
        y='B',
        text='emoji',
        hover_data=['index'],
        backend='plotly',
        labels={'A': '', 'B': ''},
        template='plotly_white',
    )
    if data is not None and data.get('xaxis.range[0]'):
        fig.update_xaxes(range=[x_min, x_max])
        fig.update_yaxes(range=[y_min, y_max])
    fig.update_layout(
        font=dict(
            size=24,  # Set the font size here
        )
    )
    # fig.update_traces(textfont_size=14)
    return fig


@app.callback(
    Output('emoji-result', 'children'),
    Input('my-graph', 'clickData'),
    Input('font-size-slider', 'value'),
    State('skin-tone', 'value'),
    State('gender', 'value'),
)
def custom_copy(click_data, fs, skin_tone, gender):
    if click_data and click_data.get('points', []):
        first_point = click_data['points'][0]
        try:
            theemoji = first_point['customdata'][0]
        except KeyError:
            print('key error')
            theemoji = None
            raise PreventUpdate
        print(f'returning {theemoji}')
        return make_cell(
            {
                'label': theemoji,
                'emoji': e.new_emoji_dict(theemoji)['emoji'],
                'text': 'the-clicked-emoji',
            },
            skin_tone,
            gender,
            fs,
        )  # includes headers
    raise PreventUpdate


if __name__ == '__main__':
    app.run_server(debug=True)
