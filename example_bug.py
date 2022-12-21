import dash_bootstrap_components as dbc
from dash import html

table_header = [
    html.Thead(html.Tr([html.Th("First Name"),
                        html.Th("Last Name")]))
]

from dash import Dash, dcc, html
from dash.dependencies import Input, Output

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
)

ALLOWED_TYPES = (
    "text",
    "number",
    "password",
    "email",
    "search",
    "tel",
    "url",
    "range",
    "hidden",
)
button_class = 'btn btn-outline-primary'


def generate_row(k):
    return html.Tr([
        html.Td(
            dbc.Button(children=f"No Outline {i}_{k}",
                       id=f"{i}_{k}",
                       className=button_class)) for i in range(2)
    ])


table_body = [html.Tbody([generate_row(k) for k in range(2)])]

table = dbc.Table(table_header + table_body, bordered=True)

app.layout = dbc.Container(
    [table, dbc.Button("Not working", class_name=button_class)])

if __name__ == "__main__":
    app.run_server(debug=True)