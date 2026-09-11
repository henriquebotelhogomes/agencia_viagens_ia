"""Compilação de GIF animado de demonstração para o README."""

from pathlib import Path

from PIL import Image


def main() -> None:
    frames_dir = Path("screenshots/frames")
    output_gif = Path("screenshots/demo.gif")

    frame_files = sorted(frames_dir.glob("frame_*.png"))
    if not frame_files:
        print("Nenhum frame encontrado em screenshots/frames!")
        return

    images: list[Image.Image] = []
    durations: list[int] = []
    target_width = 1000

    highlight_keys = ("01", "04", "05", "06", "07")

    for f in frame_files:
        im = Image.open(f).convert("RGB")
        ratio = target_width / im.width
        target_height = int(im.height * ratio)
        resized = im.resize((target_width, target_height), Image.Resampling.LANCZOS)
        paletted = resized.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        images.append(paletted)

        # Frame durations
        if any(k in f.name for k in highlight_keys):
            durations.append(2000)
        else:
            durations.append(1500)

    images[0].save(
        output_gif,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    file_size_mb = output_gif.stat().st_size / (1024 * 1024)
    print(
        f"GIF compilado com sucesso: {output_gif} "
        f"({file_size_mb:.2f} MB, {len(images)} quadros)"
    )


if __name__ == "__main__":
    main()
