"""Export the code-native Rafiq Baz heart mark for web and mobile app bundles."""
from pathlib import Path
from math import sin, cos, pi
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
image = Image.new("RGB", (1024, 1024), "#09090b")
draw = ImageDraw.Draw(image)
points = []
for step in range(1201):
    t = step * 2 * pi / 1200
    x = 16 * sin(t)**3
    y = 13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t)
    points.append((512+x*21, 490-y*21))
draw.polygon(points, fill="#f32649")
draw.ellipse((765, 202, 823, 260), fill="#f4f3f5")
foreground = Image.new("RGBA", (1024, 1024))
foreground_draw = ImageDraw.Draw(foreground)
foreground_draw.polygon(points, fill="#f32649")
foreground_draw.ellipse((765, 202, 823, 260), fill="#f4f3f5")
assets = ROOT / "public/assets"
for size in (192, 512):
    image.resize((size, size), Image.Resampling.LANCZOS).save(assets/f"icon-{size}.png", optimize=True)
ios = ROOT / "ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png"
if ios.parent.exists():
    image.save(ios, optimize=True)
android = ROOT / "android/app/src/main/res"
for density, size in (("mdpi",48),("hdpi",72),("xhdpi",96),("xxhdpi",144),("xxxhdpi",192)):
    folder = android / f"mipmap-{density}"
    if folder.exists():
        for filename in ("ic_launcher.png", "ic_launcher_round.png"):
            image.resize((size, size), Image.Resampling.LANCZOS).save(folder/filename, optimize=True)
        edge = int(size * 2.25)
        foreground.resize((edge, edge), Image.Resampling.LANCZOS).save(folder/"ic_launcher_foreground.png", optimize=True)
for splash in list(android.glob("drawable*/splash.png")) + list((ROOT/"ios/App/App/Assets.xcassets/Splash.imageset").glob("*.png")):
    with Image.open(splash) as original:
        size = original.size
    canvas = Image.new("RGB", size, "#09090b")
    edge = int(min(size) * .28)
    mark = image.resize((edge, edge), Image.Resampling.LANCZOS)
    canvas.paste(mark, ((size[0]-edge)//2, (size[1]-edge)//2))
    canvas.save(splash, optimize=True)
print("Web, Android and iOS brand icons exported.")
