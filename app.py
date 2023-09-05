from shiny import App, render, ui, experimental
from EmojiFinder import EmojiFinderSql
import sys

sys.path.append("../shiny_tables")

from shiny_tables import enhanced_from_dataframe

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
        ui.markdown("""
Shiny implementation of my Emoji semantic search. See the [Shiny branch](https://github.com/astrowonk/emoji_finder/tree/shiny) on Github for more.

Bootstrap result tables powered by my [shiny_tables](https://github.com/astrowonk/shiny_tables) module, which turns dataframes into nice bootstrap tables.
"""),
        ui.input_text(
            "search",
            "Search",
            placeholder=
            "Search for emoji (mostly limited to single words; or try an emoji like 🎟️)"
        ),
        ui.output_ui("emoji_results"),
    )
])


def process_additional_emojis(item):
    additional_emojis = e.add_variants(item['label'])
    return [{
        'emoji': e.emoji_dict[x]['emoji'],
        'text': e.emoji_dict[x]['text'],
        'label': x
    } for x in additional_emojis]


def wrap_emoji(row):
    return ui.tags.div([
        ui.tags.div(
            experimental.ui.tooltip(
                ui.tags.div(
                    row['emoji'], {
                        'style':
                        'font-size: 3em; margin-left: .75em;  display: inline-block'
                    }), row['text']),
            ui.tags.button(
                ui.tags.i({"class": "bi bi-clipboard"}, ),
                {"x-clipboard": 'input'},
                {
                    "style":
                    "margin-left: .75em; display: inline-block; margin:auto"
                },
                {"class": "btn btn-outline-secondary btn-sm"},
            ))
    ], {'x-data': f"""{{input: '{row["emoji"]}'}}"""})


def process_one_emoji(row, _):
    more_emojis = process_additional_emojis(row)
    if not more_emojis:
        return wrap_emoji(row)
    else:
        items = [wrap_emoji(row) for row in more_emojis]
        return [
            wrap_emoji(row),
            experimental.ui.accordion(experimental.ui.accordion_panel(
                "More",
                *items,
                open=False,
            ),
                                      open=False)
        ]


def server(input, output, session):

    @output
    @render.ui
    def emoji_results():
        out = e.top_emojis(input.search())
        if not out.empty:
            return enhanced_from_dataframe(
                out,
                column_callable_dict={'emoji': process_one_emoji},
                columns=['text', 'emoji'])
        return None


app = App(app_ui, server, debug=True)
