from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL

import dash_bootstrap_components as dbc

app = Dash(__name__, suppress_callback_exceptions=True)

buttons = html.Div(children=[
    dbc.Button(f"hello {i}", id={
        'index': str(i),
        'type': 'my-button'
    }) for i in range(5)
])

outputs = html.Div(children=[
    html.Div(id={
        'index': str(i),
        'type': 'my-out'
    }) for i in range(5)
])

layout = dbc.Container([buttons, outputs])

app.layout = layout


@app.callback(
    Output({'type':'my-out','index':MATCH}, 'children'),
    Input({
        'index': MATCH,
        'type': 'my-button'
    }, 'n_clicks'),
)
def display_dropdowns(n_clicks):
    print('hello')


if __name__ == '__main__':
    app.run_server(debug=True)