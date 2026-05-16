---
name: skia
description: >-
  [SDK · 2D graphics] Skia and SkiaSharp — canvas/paint/path surfaces, shaders,
  headless PNG, MAUI PaintSurface. Use when user mentions Skia, SKCanvas,
  GPU/CPU raster — not generic charting APIs (pair with `scott-plot` for plotted
  data series).
metadata:
  skill_class: sdk
  taxonomy: graphics-skia
  stack: dotnet
  discovers_with: Skia,SkiaSharp,SKCanvas,SKPaint,bitmap,PNG,GPU,MAUI renders,vectors
  integrations: SkiaSharp Core
  pairs_with: scott-plot
triggers:
  - SkiaSharp
  - SKCanvas drawing
  - render PNG without UI
---

# Skia & SkiaSharp

## Core Types

- `SKCanvas` — drawing context; immediate-mode with matrix and clip stack.
- `SKPaint` — draw state: color, stroke, shader, blend mode, filter.
- `SKPath` — vector geometry; fill, stroke, or clip.
- `SKSurface` — render target (CPU bitmap or GPU texture).
- `SKImage` — immutable snapshot of a surface or bitmap.

## Local References

| Topic | File |
|-------|------|
| Coordinates, colors, simple shapes | `references/basics.md` |
| Vector geometry, stroke caps, dashes | `references/paths.md` |
| Translate, rotate, scale, matrix, Save/Restore | `references/transforms.md` |
| Béziers, arcs, SVG path data, clipping | `references/curves.md` |
| Load, save, draw, pixel access | `references/bitmaps.md` |
| Shaders, gradients, blend modes, filters | `references/effects.md` |
| 3D transforms, Perlin noise, vertex meshes | `references/gallery.md` |

## Headless Rendering

```csharp
using var bmp = new SKBitmap(640, 480);
using var canvas = new SKCanvas(bmp);
canvas.Clear(SKColors.White);
// draw ...
using var image = SKImage.FromBitmap(bmp);
using var data = image.Encode(SKEncodedImageFormat.Png, 100);
data.SaveTo(File.OpenWrite("output.png"));
```

## UI Integration (.NET MAUI / WinForms)

Use the `PaintSurface` event on `SKCanvasView` or `SKGLControl`.

```csharp
void OnPaintSurface(object sender, SKPaintSurfaceEventArgs e)
{
    SKCanvas canvas = e.Surface.Canvas;
    canvas.Clear(SKColors.CornflowerBlue);
    // use e.Info for dimensions
}
```

## External Resources

- [SkiaSharp Guides](https://mono.github.io/SkiaSharp/docs/guides/index.html)
- [SkiaSharp API Reference](https://learn.microsoft.com/dotnet/api/skiasharp)
- [C# Data Visualization — S. Harden](https://swharden.com/csdv/skiasharp/)
- [SkiaSharp Gallery](https://mono.github.io/SkiaSharp/gallery/)
