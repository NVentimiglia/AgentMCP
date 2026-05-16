# SkiaSharp Effects

Effects allow you to alter the normal display of graphics through shaders, filters, and blend modes.

## Shaders (Gradients and Patterns)

- **Linear Gradient**: `SKShader.CreateLinearGradient(...)`
- **Radial Gradient**: `SKShader.CreateRadialGradient(...)`
- **Bitmap Tiling**: `SKShader.CreateBitmap(...)`

### Example: Linear Gradient
```csharp
SKColor[] colors = { SKColors.Blue, SKColors.Red };
float[] points = { 0, 1 };
paint.Shader = SKShader.CreateLinearGradient(
    new SKPoint(0, 0),
    new SKPoint(255, 255),
    colors,
    points,
    SKShaderTileMode.Clamp);
```

## Blend Modes

Blend modes govern how source pixels combine with destination pixels.

- **Porter-Duff**: `Src`, `Dst`, `SrcOver`, `DstOver`, `SrcIn`, `DstIn`, etc.
- **Separable**: `Multiply`, `Screen`, `Overlay`, `Darken`, `Lighten`, etc.
- **Non-Separable**: `Hue`, `Saturation`, `Color`, `Luminosity`.

```csharp
paint.BlendMode = SKBlendMode.Multiply;
```

## Mask Filters (Blur and Alpha)

Mask filters apply to the alpha channel before the color is applied.

- **Blur**: `SKMaskFilter.CreateBlur(...)`

```csharp
paint.MaskFilter = SKMaskFilter.CreateBlur(SKBlurStyle.Normal, 5);
```

## Image Filters (Post-Processing)

Image filters apply to the entire resulting image.

- **Blur**: `SKImageFilter.CreateBlur(...)`
- **Drop Shadow**: `SKImageFilter.CreateDropShadow(...)`
- **Matrix**: `SKImageFilter.CreateColorFilter(...)`

```csharp
paint.ImageFilter = SKImageFilter.CreateDropShadow(5, 5, 3, 3, SKColors.Black);
```

## Color Filters

Color filters transform each pixel's color.

- **Color Matrix**: `SKColorFilter.CreateColorMatrix(...)`
- **Blend Mode Filter**: `SKColorFilter.CreateBlendMode(...)`

```csharp
float[] matrix = {
    0.393f, 0.769f, 0.189f, 0, 0, // Red
    0.349f, 0.686f, 0.168f, 0, 0, // Green
    0.272f, 0.534f, 0.131f, 0, 0, // Blue
    0,      0,      0,      1, 0  // Alpha
};
paint.ColorFilter = SKColorFilter.CreateColorMatrix(matrix);
```
