# SkiaSharp Transforms

Transforms allow you to manipulate the coordinate system used for drawing.

## Common Transforms

- **`Translate(x, y)`**: Shifts the coordinate system.
- **`Scale(sx, sy)`**: Scales the coordinate system (optionally around a pivot point).
- **`RotateDegrees(degrees, px, py)`**: Rotates the coordinate system around a pivot point.
- **`Skew(sx, sy)`**: Skews the coordinate system.

## Lifecycle Management

- **`Save()`**: Saves the current transform and clip state.
- **`Restore()`**: Restores the last saved state.
- **`SKAutoCanvasRestore`**: A disposable wrapper that automatically calls `Restore()` when disposed.

## Examples

### Using Save/Restore
```csharp
using (new SKAutoCanvasRestore(canvas))
{
    canvas.Translate(100, 100);
    canvas.RotateDegrees(45);
    canvas.DrawRect(0, 0, 50, 50, paint);
}
// Coordinate system is back to normal here
```

### Rotating Around a Point
```csharp
// Rotate 45 degrees around (width/2, height/2)
canvas.RotateDegrees(45, info.Width / 2, info.Height / 2);
canvas.DrawRect(rect, paint);
```

### Concatenating Transforms
Transforms are cumulative.
```csharp
canvas.Translate(100, 100);
canvas.Scale(2, 2);
// Subsequently drawn items are translated AND scaled.
```

### Matrix Transforms
For advanced manipulations, use `SKMatrix`.
```csharp
SKMatrix matrix = SKMatrix.CreateTranslation(100, 100);
matrix = matrix.PostConcat(SKMatrix.CreateRotationDegrees(45));
canvas.SetMatrix(matrix);
```

### Non-Affine (Perspective) Transforms
Use `SKMatrix` with the 3x3 values.
```csharp
SKMatrix matrix = SKMatrix.Identity;
matrix.Persp0 = 0.001f; // Perspective effect
canvas.SetMatrix(matrix);
```
