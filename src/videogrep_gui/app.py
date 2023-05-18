"""
Videogrep gui
"""
import asyncio
import os
from collections import Counter

import toga
import videogrep
from toga.style.pack import CENTER, COLUMN, ROW, Pack
from videogrep import transcribe


class VideogrepGui(toga.App):
    def startup(self):
        self.videos = []
        self.has_loaded = False
        self.working = False

        self.main_window = toga.MainWindow(title=self.name, size=(1000, 600))

        self.working_box = toga.Box(
            children=[
                toga.Box(style=Pack(flex=1)),
                toga.Box(children=[toga.Label("Working...")]),
                toga.Box(style=Pack(flex=1)),
            ],
            style=Pack(direction=COLUMN, alignment=CENTER),
        )

        self.files_list = toga.MultilineTextInput(
            readonly=True,
            style=Pack(background_color="#fff", padding_top=10, padding_bottom=10),
        )

        self.left_box = toga.Box(
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
                            on_select=self.search,
                            style=Pack(padding_right=10),
                        ),
                        toga.Button("Search", on_press=self.search),
                    ]
                ),
                toga.Divider(
                    style=Pack(padding_bottom=20, padding_top=20),
                ),
                toga.Box(
                    children=[
                        toga.Label("Padding (ms)", style=Pack(padding_right=10)),
                        toga.NumberInput(
                            min_value=0, max_value=1000, step=1, value=0, id="padding"
                        ),
                    ]
                ),
                toga.Box(
                    children=[
                        toga.Label("Shift (ms)", style=Pack(padding_right=10)),
                        toga.NumberInput(
                            min_value=-1000,
                            max_value=1000,
                            step=1,
                            value=0,
                            id="resync",
                        ),
                    ],
                    style=Pack(padding_top=10),
                ),
            ],
            style=Pack(padding=20, flex=1, direction=COLUMN),
        )

        analysis_box = toga.Box(
            style=Pack(flex=1, padding=10, direction=COLUMN),
            children=[
                toga.Box(
                    children=[
                        toga.Label(
                            "Frequent words in groups of", style=Pack(padding_right=10)
                        ),
                        toga.NumberInput(
                            min_value=1,
                            max_value=10,
                            step=1,
                            value=1,
                            id="ngrams",
                            on_change=self.get_ngrams,
                        ),
                    ]
                ),
                toga.MultilineTextInput(
                    id="ngrams_holder",
                    readonly=True,
                    style=Pack(
                        flex=1,
                        padding_top=10,
                        font_family="monospace",
                    ),
                ),
            ],
        )

        results_box = toga.Box(
            children=[
                toga.MultilineTextInput(
                    id="results",
                    readonly=True,
                    style=Pack(
                        direction=COLUMN,
                        flex=1,
                        padding=0,
                        font_family="monospace",
                    ),
                )
            ],
            style=Pack(direction=COLUMN, padding=10),
        )

        export_buttons = toga.Box(
            children=[
                toga.Box(style=Pack(flex=1)),
                toga.Button(
                    "Preview",
                    on_press=self.preview,
                    style=Pack(padding_right=10),
                ),
                toga.Button("Export", on_press=self.export),
            ],
            style=Pack(padding=(0, 20, 20, 20))

        )

        self.right_box = toga.OptionContainer(style=Pack(flex=1, padding=20))
        self.right_box.add("Search Results", results_box)
        self.right_box.add("Common Words", analysis_box)

        self.main_box = toga.Box(
            style=Pack(direction=ROW),
            children=[
                self.left_box,
                toga.Divider(direction=1),
                toga.Box(
                    style=Pack(direction=COLUMN, flex=1),
                    children=[self.right_box, export_buttons],
                ),
            ],
        )
        # self.main_box.style.padding = 20

        self.main_window.content = self.main_box

        # Show the main window
        self.main_window.show()

    def get_ngrams(self, _n):
        if len(self.videos) == 0:
            return False
        n = int(self.widgets.get("ngrams").value)
        grams = videogrep.get_ngrams(self.videos, n=n)

        most_common = Counter(grams).most_common(100)

        out = []

        for ngram, count in most_common:
            out.append(" ".join(ngram) + " (" + str(count) + ")")

        self.widgets.get("ngrams_holder").value = "\n".join(out)

    async def transcribe(self, button):
        if len(self.videos) == 0:
            return False

        self.toggle_work()

        def render():
            for f in self.videos:
                transcribe.transcribe(f)

        await asyncio.get_event_loop().run_in_executor(None, render)
        self.post_load()

        self.toggle_work()

    async def preview(self, button):
        try:
            q = self.widgets.get("q").value
            if len(self.videos) == 0 or q.strip() == "":
                return False
            search_type = {"Sentences": "sentence", "Words": "fragment"}[
                self.widgets.get("search_type").value
            ]

            pad = float(self.widgets.get("padding").value)
            if pad != 0:
                pad = pad / 1000

            resync = float(self.widgets.get("resync").value)
            if resync != 0:
                resync = resync / 1000

            composition = videogrep.search(
                files=self.videos,
                query=q,
                search_type=search_type,
            )
            composition = videogrep.pad_and_sync(
                composition, padding=pad, resync=resync
            )

            lines = []
            for c in composition:
                lines.append(
                    f"{os.path.abspath(c['file'])},{c['start']},{c['end']-c['start']}"
                )

            edl = "edl://" + ";".join(lines)

            proc = await asyncio.create_subprocess_exec("mpv", edl, "--loop")

        except Exception as e:
            result = await self.main_window.confirm_dialog(
                "Unable to Preview",
                "MPV is required to preview. Would you like to download it now?",
            )
            if result:
                import webbrowser

                webbrowser.open("https://mpv.io/")
                return False

    async def export(self, button):
        q = self.widgets.get("q").value
        if len(self.videos) == 0 or q.strip() == "":
            return False

        try:
            output = await self.main_window.save_file_dialog(
                "Save as", "supercut.mp4", file_types=["mp4"]
            )
            if output is not None:
                output = str(output)

                search_type = {"Sentences": "sentence", "Words": "fragment"}[
                    self.widgets.get("search_type").value
                ]

                pad = float(self.widgets.get("padding").value)
                if pad != 0:
                    pad = pad / 1000

                resync = float(self.widgets.get("resync").value)
                if resync != 0:
                    resync = resync / 1000

                self.toggle_work()

                def render():
                    videogrep.videogrep(
                        files=self.videos,
                        query=q,
                        search_type=search_type,
                        padding=pad,
                        resync=resync,
                        output=output,
                    )

                await asyncio.get_event_loop().run_in_executor(None, render)
                self.toggle_work()

        except Exception as e:
            print(e)

    def toggle_work(self):
        self.working = not self.working

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
                    # if not self.has_loaded:
                    #     self.main_window.content = self.main_box
                    #     self.has_loaded = True
                    self.post_load()
            else:
                print("none")
        except ValueError:
            pass

    def post_load(self):
        self.get_ngrams(None)
        self.search(None)


def main():
    return VideogrepGui("Videogrep", "lav.io.videogrep")
