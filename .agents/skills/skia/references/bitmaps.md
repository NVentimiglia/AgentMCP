# SkiaSharp Bitmaps

Bitmaps are rectangular arrays of pixel data.

## Key Classes

- **`SKBitmap`**: The main bitmap class.
- **`SKImage`**: An immutable version of a bitmap, often used for snapshots or optimized drawing.
- **`SKCodec`**: Used for decoding bitmap files (PNG, JPEG, etc.).

## Examples

### Loading a Bitmap
```csharp
using (var stream = new SKFileStream("image.png"))
{
    using (var bitmap = SKBitmap.Decode(stream))
    {
        // Use the bitmap
    }
}
```

### Drawing a Bitmap
```csharp
canvas.DrawBitmap(bitmap, 100, 100, paint);

// Scaling a bitmap to a rectangle
SKRect destRect = new SKRect(0, 0, info.Width, info.Height);
canvas.DrawBitmap(bitmap, destRect, paint);
```

### Creating and Drawing on a Bitmap
```csharp
SKBitmap bitmap = new SKBitmap(640, 480);
using (SKCanvas bitmapCanvas = new SKCanvas(bitmap))
{
    bitmapCanvas.Clear(SKColors.White);
    bitmapCanvas.DrawCircle(320, 240, 100, paint);
}
```

### Saving a Bitmap
```csharp
using (SKImage image = SKImage.FromBitmap(bitmap))
using (SKData data = image.Encode(SKEncodedImageFormat.Png, 100))
using (var stream = File.OpenWrite("output.png"))
{
    data.SaveTo(stream);
}
```

### Accessing Pixel Bits (Fast)
Use `GetPixelSpan` for efficient access.
```csharp
ReadOnlySpan<SKColor> pixels = bitmap.GetPixelSpan<SKColor>();
for (int i = 0; i < pixels.Length; i++)
{
    SKColor color = pixels[i];
    // Process color
}
```

### Nine-Patch and Lattice
Use `DrawBitmapNinePatch` for buttons or UI elements that should scale without distorting corners.
```csharp
SKRectI center = new SKRectI(10, 10, 20, 20);
canvas.DrawBitmapNinePatch(bitmap, center, destRect, paint);
```
