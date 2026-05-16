# SkiaSharp Drawing Basics

Learn the core concepts of SkiaSharp graphics: coordinates, paints, and basic shapes.

## Core Classes

- **`SKCanvas`**: The drawing surface. All drawing commands are methods on this class.
- **`SKPaint`**: Holds the style information for drawing (color, stroke width, anti-aliasing, etc.).
- **`SKBitmap`**: A rectangular array of pixels.
- **`SKSurface`**: Manages a drawing destination (memory, GPU, etc.).

## Coordinates and Units

- **Pixels**: SkiaSharp draws in pixels.
- **Device-Independent Units (DIUs)**: .NET MAUI and other frameworks use DIUs.
- **Scaling**: Use `canvas.Scale()` or calculate the ratio between DIUs and pixels to ensure consistent rendering across high-DPI displays.

## Examples

### Drawing a Simple Circle
```csharp
void OnCanvasViewPaintSurface(object sender, SKPaintSurfaceEventArgs args)
{
    SKImageInfo info = args.Info;
    SKSurface surface = args.Surface;
    SKCanvas canvas = surface.Canvas;

    canvas.Clear();

    SKPaint paint = new SKPaint
    {
        Style = SKPaintStyle.Fill,
        Color = SKColors.Blue,
        StrokeWidth = 10,
        IsAntialias = true
    };

    canvas.DrawCircle(info.Width / 2, info.Height / 2, 100, paint);
}
```

### Drawing Rectangles and Ovals
```csharp
SKRect rect = new SKRect(100, 100, 300, 200);
canvas.DrawRect(rect, paint);

canvas.DrawOval(rect, paint);
```

### Basic Text Rendering
```csharp
SKPaint textPaint = new SKPaint
{
    Color = SKColors.Black,
    TextSize = 64,
    IsAntialias = true
};

canvas.DrawText("Hello SkiaSharp!", 100, 100, textPaint);

// Measuring text
SKRect textBounds = new SKRect();
textPaint.MeasureText("Hello SkiaSharp!", ref textBounds);
```

### Transparency and Blending
```csharp
paint.Color = paint.Color.WithAlpha(128); // 50% transparent
```
