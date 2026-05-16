# SkiaSharp Lines and Paths

Paths are the most powerful way to draw complex vector geometry in SkiaSharp.

## SKPath Basics

- **`MoveTo(x, y)`**: Starts a new contour at the specified point.
- **`LineTo(x, y)`**: Adds a line from the last point to the specified point.
- **`ArcTo(rect, startAngle, sweepAngle, forceMoveTo)`**: Adds an arc.
- **`Close()`**: Closes the current contour by adding a line back to the start.

## Examples

### Creating and Drawing a Path
```csharp
SKPath path = new SKPath();
path.MoveTo(100, 100);
path.LineTo(200, 200);
path.LineTo(100, 200);
path.Close();

canvas.DrawPath(path, paint);
```

### Stroke Caps and Joins
```csharp
SKPaint paint = new SKPaint
{
    Style = SKPaintStyle.Stroke,
    Color = SKColors.Red,
    StrokeWidth = 20,
    StrokeCap = SKStrokeCap.Round, // Butt, Round, Square
    StrokeJoin = SKStrokeJoin.Round // Miter, Round, Bevel
};
```

### Dashing and Dotting
```csharp
// Create a dash effect: 10 pixels on, 5 pixels off
float[] intervals = { 10, 5 };
paint.PathEffect = SKPathEffect.CreateDash(intervals, 0);

canvas.DrawPath(path, paint);
```

### Fill Types
- **`Winding`**: Default. A point is inside if its winding number is non-zero.
- **`EvenOdd`**: A point is inside if it's crossed by an odd number of boundary edges.

```csharp
path.FillType = SKPathFillType.EvenOdd;
```

### Path Effects
```csharp
// Discrete effect (roughen lines)
paint.PathEffect = SKPathEffect.CreateDiscrete(10, 5);

// Corner effect (round corners of a path)
paint.PathEffect = SKPathEffect.CreateCorner(20);
```
