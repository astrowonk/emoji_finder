from shiny import App, render, ui, experimental
from EmojiFinder import EmojiFinderSql

STYLE = {"marginBottom": 20, "marginTop": 20, 'width': '85%'}

e = EmojiFinderSql()
app_ui = ui.page_bootstrap([
    ui.head_content(
        ui.tags.script({
            "src":
            "https://cdn.jsdelivr.net/npm/@ryangjchandler/alpine-clipboard@2.x.x/dist/alpine-clipboard.js"
        }),
        ui.tags.script({
            "src":
            "https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"
        }),
        ui.tags.link({
            "href":
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css",
            "rel": "stylesheet"
        })),
    ui.tags.div(
        {
            'class': 'container',
            'style': 'marginTop: 20, marginTop: 20, width: 85%'
        },
        ui.panel_title("Emoji Semantic Search with Shiny!"),
        ui.markdown("""Shiny implementation of my Emoji semantic search. See the [Shiny branch](https://github.com/astrowonk/emoji_finder/tree/shiny) on Github for more."""),
        ui.input_text("search", "Search", placeholder="Search emoji"),
        ui.output_ui("txt"),
    )
])


def process_additional_emojis(item):
    additional_emojis = e.add_variants(item['label'])
    return [{
        'emoji': e.emoji_dict[x]['emoji'],
        'text': e.emoji_dict[x]['text'],
        'label': x
    } for x in additional_emojis]


def wrap_emoji(emoji):
    return ui.tags.div([
        ui.tags.div(
            ui.tags.div(
                emoji, {
                    'style':
                    'font-size: 3em; margin-left: .75em;  display: inline-block'
                }),
            ui.tags.button(
                ui.tags.i({"class": "bi bi-clipboard"}, ),
                {"x-clipboard": 'input'},
                {
                    "style":
                    "margin-left: .75em; display: inline-block; margin:auto"
                },
                {"class": "btn btn-outline-secondary btn-sm"},
            ))
    ], {'x-data': f"{{input: '{emoji}'}}"})


def process_one_emoji(row):
    more_emojis = process_additional_emojis(row)
    if not more_emojis:
        return wrap_emoji(row['emoji'])
    else:
        items = [wrap_emoji(x['emoji']) for x in more_emojis]
        return [
            wrap_emoji(row['emoji']),
            experimental.ui.accordion(experimental.ui.accordion_panel(
                "More",
                *items,
                open=False,
            ),
                                      open=False)
        ]


def make_row(row, i):
    return ui.tags.tr([
        ui.tags.td(row['text']),
        ui.tags.td(process_one_emoji(row)),
    ])


def make_my_table(rows):
    out = ui.tags.table(
        {'class': 'table w-75 table-striped'},
        ui.tags.thead(ui.tags.tr([ui.tags.th("Label"),
                                  ui.tags.th("Emoji")])),
        ui.tags.tbody([make_row(x, i) for i, x in enumerate(rows)]),
    )
    #print(out)
    return out


def server(input, output, session):

    @output
    @render.ui
    def txt():
        out = e.top_emojis(input.search()).to_dict(orient='records')
        print(type(out))
        if out:
            return make_my_table(out)
        return None


app = App(app_ui, server, debug=True)
