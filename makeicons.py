from subprocess import run

icons = {
    "ico": [16, 32, 48, 64, 256],
    "icns": [None, 16, 32, 48, 128, 256, 512, 1024],
    "png": [None, 16, 32, 64, 128, 256, 512],
}

for ext, sizes in icons.items():

    for s in sizes:
        if s is None:
            args = [
                "convert",
                "icon.png",
                f"src/videogrep_gui/resources/videogrep_gui.{ext}",
            ]
        else:
            args = [
                "convert",
                "icon.png",
                "-resize",
                f"{s}x{s}",
                f"src/videogrep_gui/resources/videogrep_gui-{s}.{ext}",
            ]
        run(args)
