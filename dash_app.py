from dash import Output, Input, html, State, MATCH, ALL, dcc, Dash, callback_context
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
import dash_dataframe_table

from EmojiFinder import EmojiFinderSql, SKIN_TONE_SUFFIXES
from pathlib import Path

parent_dir = Path().absolute().stem

e = EmojiFinderSql()

app = Dash(__name__,
           url_base_pathname=f"/dash/{parent_dir}/",
           external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
           title="Emoji Semantic Search",
           meta_tags=[
               {
                   "name": "viewport",
                   "content": "width=device-width, initial-scale=1"
               },
           ])
server = app.server
STYLE = {"marginBottom": 20, "marginTop": 20, 'width': '75%'}

range_slider = html.Div(
    [
        dbc.Label("Font Size", html_for="font-size-slider"),
        dcc.Slider(id="font-size-slider",
                   min=1,
                   max=4,
                   step=.5,
                   value=3,
                   persistence=True),
    ],
    className="mb-3",
)

layout = dbc.Container(children=[
    html.H3('Emoji Semantic Search', style={'text-align': 'center'}),
    dbc.Button('Settings',
               id='expand-prefs',
               class_name='btn-secondary btn-sm'),
    dbc.Collapse([
        range_slider,
        dcc.Dropdown(id='skin-tone',
                     options=SKIN_TONE_SUFFIXES,
                     persistence=True,
                     placeholder='Skin Tone search priority...'),
        dcc.Dropdown(id='gender',
                     options=['man', 'woman'],
                     persistence=True,
                     placeholder="Gender search priority..."),
    ],
                 id='search-priorities',
                 is_open=False),
    dbc.InputGroup([
        dbc.InputGroupText(
            html.I(className="bi bi-search", style={'float': 'left'})),
        dbc.Input(
            id='search-input',
            value='',
            debounce=True,
            placeholder='Search for emoji (mostly limited to single words; or try an emoji like 🎟️)',
        ),
    ],
                   style=STYLE),
    dcc.Markdown(
        "Source code and more info on [Github](https://github.com/astrowonk/emoji_finder)."
    ),
    html.Div(id='results')
],
                       style=STYLE)

app.layout = layout


def wrap_emoji(record, font_size):
    return html.Div([
        html.P(record['emoji'],
               id=record['text'],
               style={'font-size': f'{font_size}em'}),
        dcc.Clipboard(target_id=record['text'],
                      style={
                          'top': '-55px',
                          'right': '-65px',
                          'position': 'relative'
                      }),
    ],
                    className='emoji')


def make_cell(item, skin_tone, gender, font_size):
    if not skin_tone:
        skin_tone = ''
    if not gender:
        gender = ''
    additional_emojis = e.add_variants(item['label'])
    additional_emojis = [{
        'emoji': e.emoji_dict[x]['emoji'],
        'text': e.emoji_dict[x]['text'],
        'key': x
    } for x in additional_emojis]
    priority_result = []
    gender_result = []
    if skin_tone:
        priority_result = [
            x for x in additional_emojis if x['key'].endswith(skin_tone + ':')
        ]
    if gender:
        gender_result = [
            x for x in priority_result or additional_emojis
            if x['key'].startswith(':' + gender)
        ]
    if gender_result:
        priority_result = gender_result

    if priority_result:
        priority_result = priority_result[0]
        #   print('PRIORITY')
        #   print(priority_result)
        #   print("ALL ADDITIONAL")
        #   print(additional_emojis)
        additional_emojis.remove(priority_result)
        target = priority_result
    else:
        target = item
    if additional_emojis:
        return [
            html.Div(wrap_emoji(target, font_size)),
            dbc.Button('More',
                       id={
                           'type': 'more-button',
                           'index': item['text']
                       },
                       className="btn-secondary btn-sm"),
            dbc.Collapse(
                [wrap_emoji(item, font_size) for item in additional_emojis],
                id={
                    'type': 'more-emojis',
                    'index': item['text']
                },
                is_open=False)
        ]
    return html.Div(wrap_emoji(item, font_size=font_size))


def make_table_row(record, skin_tone, gender, font_size):
    return html.Tr([
        html.Td(record['text'].title()),
        html.Td(make_cell(record, skin_tone, gender, font_size))
    ],
                   style={'margin': 'auto'})


@app.callback(
    Output('results', 'children'),
    Input('search-input', 'value'),
    Input('skin-tone', 'value'),
    Input('gender', 'value'),
    Input('font-size-slider', 'value'),
)
def search_results(search, skin_tone, gender, font_size):
    if search:
        full_res = e.top_emojis(search)
        if full_res.empty:
            return html.H3('No Results')
        res_list = full_res.to_dict('records')
        variants = []
        for rec in res_list:
            variants.extend(e.add_variants(rec['label']))
        ## remove variants from list
        full_res = full_res.query("label not in @variants")
        table_header = [
            html.Thead(html.Tr([html.Th("Description"),
                                html.Th("Emoji")]))
        ]
        table_rows = [
            make_table_row(rec, skin_tone, gender, font_size)
            for rec in full_res.to_dict('records')
        ]
        table_body = [html.Tbody(table_rows)]
        return dbc.Table(table_header + table_body,
                         bordered=False,
                         striped=True)

    return html.H3('No Results')


@app.callback(
    Output({
        'type': 'more-emojis',
        'index': MATCH
    }, 'is_open'),
    State({
        'type': 'more-emojis',
        'index': MATCH
    }, 'is_open'),
    Input({
        'type': 'more-button',
        'index': MATCH
    }, 'n_clicks'),
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


if __name__ == "__main__":
    app.run_server(debug=True)
