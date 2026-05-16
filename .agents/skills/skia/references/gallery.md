# SkiaSharp Gallery Examples

Advanced snippets and techniques from the official SkiaSharp gallery.

## 3D Transforms (Perspective)

You can create 3D-like effects using non-affine matrix transforms.

```csharp
void Draw3D(SKCanvas canvas, float rotationX, float rotationY)
{
    var info = canvas.DeviceClipBounds;
    var center = new SKPoint(info.Width / 2f, info.Height / 2f);

    var matrix = SKMatrix.CreateIdentity();
    
    // Perspective
    matrix.Persp0 = 0.001f; 
    matrix.Persp1 = 0.0005f;

    // Rotation
    var rotation = SKMatrix.CreateRotationDegrees(rotationY, center.X, center.Y);
    matrix = matrix.PostConcat(rotation);

    canvas.SetMatrix(matrix);
    canvas.DrawRect(SKRect.Create(center.X - 100, center.Y - 100, 200, 200), paint);
}
```

## Advanced Gradients

Gradients can be combined with shaders for complex effects.

### Sweep Gradient (Conical)
```csharp
var colors = new[] { SKColors.Cyan, SKColors.Magenta, SKColors.Yellow, SKColors.Cyan };
var shader = SKShader.CreateSweepGradient(center, colors, null);
paint.Shader = shader;
canvas.DrawCircle(center, radius, paint);
```

### Two-Point Conical Gradient
```csharp
var shader = SKShader.CreateTwoPointConicalGradient(
    startCenter, startRadius,
    endCenter, endRadius,
    colors, null, SKShaderTileMode.Clamp);
```

## Blend Modes Playground

Use blend modes to create composite effects like shadows or highlights.

```csharp
// Draw destination
canvas.DrawCircle(100, 100, 50, dstPaint);

// Draw source with blend mode
paint.BlendMode = SKBlendMode.SrcIn;
canvas.DrawRect(50, 50, 100, 100, paint);
```

## Perlin Noise

SkiaSharp can generate Perlin noise shaders for textures.

```csharp
var shader = SKShader.CreatePerlinNoiseFractalNoise(0.05f, 0.05f, 4, 0);
paint.Shader = shader;
canvas.DrawPaint(paint);
```

## Vertex Meshes

For custom deformations or complex shapes, use `DrawVertices`.

```csharp
SKPoint[] vertices = { ... };
SKColor[] colors = { ... };
canvas.DrawVertices(SKVertexMode.Triangles, vertices, null, colors, paint);
```
