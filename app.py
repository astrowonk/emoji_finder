from shiny import App, render, ui, experimental
from EmojiFinder import EmojiFinderSql

e = EmojiFinderSql()

app_ui = ui.page_fluid([
    ui.panel_title("Emoji Search for Shiny!"),
    ui.input_text("search", "Search", placeholder="Search emoji"),
    ui.output_ui("txt"),
])


def process_additional_emojis(item):
    additional_emojis = e.add_variants(item['label'])
    return [{
        'emoji': e.emoji_dict[x]['emoji'],
        'text': e.emoji_dict[x]['text'],
        'label': x
    } for x in additional_emojis]


def wrap_emoji(emoji):
    return ui.tags.p(emoji, {'style': 'font-size: 3em'})


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
        {'class': 'table w-50 table-striped'},
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
