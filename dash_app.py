from dash import Output, Input, html, State, MATCH, ALL, dcc, Dash, callback_context
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
import dash_dataframe_table

from EmojiFinder import EmojiFinderCached
from pathlib import Path

parent_dir = Path().absolute().stem

e = EmojiFinderCached()

app = Dash("emoji_finder",
           url_base_pathname=f"/dash/{parent_dir}/",
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           title="Emoji Semantic Search",
           meta_tags=[
               {
                   "name": "viewport",
                   "content": "width=device-width, initial-scale=1"
               },
           ])
server = app.server
STYLE = {"marginBottom": 30, "marginTop": 20, 'width': '75%'}

layout = dbc.Container(
    children=[
        html.Datalist(id='auto-list',
                      children=[
                          html.Option(value=word)
                          for word in sorted(list(e.vocab_dict.keys()))
                      ]),
        html.H3('Emoji Semantic Search', style={'text-align': 'center'}),
        dbc.Input(
            id='search-input',
            autoFocus=True,
            value='',
            # debounce=True,
            persistence=True,
            type='text',
            list='auto-list',
            placeholder='Search for emoji...'),
        html.Div(id='results')
    ],
    style=STYLE)

app.layout = layout


def wrap_emoji(record):
    return html.Div([
        html.P(record['emoji'], id=record['text'], style={'font-size': '3em'}),
        dcc.Clipboard(target_id=record['text'],
                      style={
                          'top': '-55px',
                          'right': '-65px',
                          'position': 'relative'
                      }),
    ])


def make_cell(item):
    additional_emojis = e.add_variants(item['label'])
    additional_emojis = [{
        'text': e.emoji_text_dict[x],
        'emoji': e.emoji_dict[x]
    } for x in additional_emojis]
    additional_emojis = sorted(additional_emojis, key=lambda x: x['text'])
    if additional_emojis:
        return [
            html.Div(wrap_emoji(item)),
            dbc.Button('More',
                       id={
                           'type': 'more-button',
                           'index': item['text']
                       },
                       className="btn-secondary btn-sm"),
            dbc.Collapse([wrap_emoji(item) for item in additional_emojis],
                         id={
                             'type': 'more-emojis',
                             'index': item['text']
                         },
                         is_open=False)
        ]
    return html.Div(wrap_emoji(item))


def make_table_row(record):
    return html.Tr(
        [html.Td(record['text'].title()),
         html.Td(make_cell(record))],
        style={'margin': 'auto'})


@app.callback(
    Output('results', 'children'),
    Input('search-input', 'value'),
)
def search_results(search):
    if search:
        full_res = e.top_emojis(search)
        if full_res.empty:
            raise PreventUpdate
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
            make_table_row(rec) for rec in full_res.to_dict('records')
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


if __name__ == "__main__":
    app.run_server(debug=True)
