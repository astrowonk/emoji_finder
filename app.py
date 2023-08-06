from shiny import App, render, ui
from EmojiFinder import EmojiFinderSql

e = EmojiFinderSql()

app_ui = ui.page_fluid([
    ui.panel_title("Emoji Search for Shiny!"),
    ui.input_text("search", "Search", placeholder="Search emoji"),
    ui.output_table("txt"),
])


def server(input, output, session):

    @output
    @render.table
    def txt():
        out = e.top_emojis(input.search())
        print(type(out))
        if out is not None and not out.empty:
            return out[['text', 'emoji']]
        return None


app = App(app_ui, server, debug=True)
