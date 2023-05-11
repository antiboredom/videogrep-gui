"""
Videogrep gui
"""
import os

import toga
import videogrep
from toga.style.pack import CENTER, COLUMN, LEFT, RIGHT, ROW, Pack
from videogrep import transcribe


class VideogrepGui(toga.App):
    def startup(self):
        self.videos = []
        self.has_loaded = False

        self.main_window = toga.MainWindow(title=self.name, size=(1000, 600))

        load_button = toga.Button(
            "Open Video(s)",
            on_press=self.load_videos,
            style=Pack(padding=0, alignment=CENTER),
        )

        self.working_box = toga.Box(
            children=[
                toga.Box(style=Pack(flex=1)),
                toga.Box(children=[toga.Label("Working...")]),
                toga.Box(style=Pack(flex=1)),
            ],
            style=Pack(direction=COLUMN, alignment=CENTER),
        )

        self.first_box = toga.Box(
            children=[
                toga.Box(style=Pack(flex=1)),
                toga.Box(children=[load_button]),
                toga.Box(style=Pack(flex=1)),
            ],
            style=Pack(direction=COLUMN, alignment=CENTER),
        )

        self.files_list = toga.MultilineTextInput(
            readonly=True,
            style=Pack(background_color="#fff", padding_top=10, padding_bottom=10),
        )

        self.left_box = toga.Box(
            # style=Pack(direction=COLUMN),
            children=[
                toga.Label("Videos"),
                self.files_list,
                toga.Box(
                    children=[
                        toga.Box(style=Pack(flex=1)),
                        toga.Button(
                            "Open New video(s)",
                            on_press=self.load_videos,
                            style=Pack(padding_right=10),
                        ),
                        toga.Button(
                            "Transcribe",
                            on_press=self.transcribe,
                        ),
                    ]
                ),
                toga.Divider(
                    style=Pack(padding_bottom=20, padding_top=20),
                ),
                toga.Box(
                    children=[
                        toga.TextInput(
                            id="q",
                            placeholder="Search",
                            on_change=self.search,
                            style=Pack(flex=1, padding_right=10),
                        ),
                        toga.Selection(
                            id="search_type",
                            items=["Sentences", "Words"],
                            style=Pack(padding_right=10),
                        ),
                        toga.Button("Search", on_press=self.search),
                    ]
                ),
            ],
            style=Pack(padding=20, flex=1, direction=COLUMN),
        )

        self.right_box = toga.Box(
            style=Pack(flex=1, padding=20, direction=COLUMN),
            children=[
                toga.Label("Results"),
                toga.MultilineTextInput(
                    id="results",
                    readonly=True,
                    style=Pack(
                        flex=1,
                        padding_top=10,
                        padding_bottom=10,
                        font_family="monospace",
                    ),
                ),
                toga.Box(
                    children=[
                        toga.Box(style=Pack(flex=1)),
                        toga.Button("Export", on_press=self.export),
                    ]
                ),
            ],
        )

        self.main_box = toga.Box(
            style=Pack(direction=ROW),
            children=[self.left_box, toga.Divider(direction=1), self.right_box],
        )
        # self.main_box.style.padding = 20

        # self.main_window.content = self.first_box
        self.main_window.content = self.main_box

        # Show the main window
        self.main_window.show()


    def transcribe(self, button):
        self.working = True
        self.toggle_work()
        for f in self.videos:
            transcribe.transcribe(f)
        self.working = False
        self.toggle_work()

    async def export(self, button):
        try:
            output = await self.main_window.save_file_dialog(
                "Save as", "supercut.mp4", file_types=["mp4"]
            )
            if output is not None:
                output = str(output)

                search_type = {"Sentences": "sentence", "Words": "fragment"}[
                    self.widgets.get("search_type").value
                ]

                q = self.widgets.get("q").value

                videogrep.videogrep(
                    files=self.videos, query=q, search_type=search_type, output=output
                )

        except Exception as e:
            print(e)

    def toggle_work(self):
        if self.working:
            self.main_window.content = self.working_box
        else:
            self.main_window.content = self.main_box

    def search(self, button):
        # print(self.widgets)
        search_type = {"Sentences": "sentence", "Words": "fragment"}[
            self.widgets.get("search_type").value
        ]

        q = self.widgets.get("q").value

        results = videogrep.search(files=self.videos, query=q, search_type=search_type)

        text_results = [
            f"{r['start']:.2f} - {r['end']:.2f}: {r['content']}" for r in results
        ]
        text_results = "\n".join(text_results)
        if text_results == "":
            text_results = "No results"

        self.widgets.get("results").value = text_results

    async def load_videos(self, button):
        try:
            paths = await self.main_window.open_file_dialog(
                "Load videos",
                multiselect=True,
                file_types=["mp4", "mov", "avi", "webm", "mkv"],
            )

            if paths is not None:
                if len(paths) > 0:
                    self.videos = [str(p) for p in paths]
                    self.files_list.value = "\n".join(
                        [os.path.basename(p) for p in self.videos]
                    )
                    self.main_window.content = self.main_box
                    self.has_loaded = True
                    print(paths)
            else:
                print("none")
        except ValueError:
            pass


def main():
    return VideogrepGui("Videogrep", "lav.io.videogrep")
