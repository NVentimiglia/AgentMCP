# SkiaSharp Curves and Advanced Paths

SkiaSharp supports various types of curves: Arcs, Bézier curves, and path data strings.

## Arcs

- **`ArcTo(rect, startAngle, sweepAngle, forceMoveTo)`**: Draws an arc as part of an ellipse.
- **`ArcTo(x1, y1, x2, y2, radius)`**: Draws an arc tangent to two lines (like a rounded corner).
- **`ArcTo(rx, ry, xAxisRotate, largeArc, sweep, x, y)`**: SVG-style arc.

## Bézier Curves

- **Quadratic**: `QuadTo(x1, y1, x2, y2)` - One control point.
- **Cubic**: `CubicTo(x1, y1, x2, y2, x3, y3)` - Two control points.
- **Conic**: `ConicTo(x1, y1, x2, y2, weight)` - Arcs of circles, ellipses, hyperbolas.

### Example: Cubic Bézier
```csharp
SKPath path = new SKPath();
path.MoveTo(100, 100);
path.CubicTo(150, 50, 250, 150, 300, 100);
canvas.DrawPath(path, paint);
```

## SVG Path Data

You can define a path using a concise text string (SVG format).

```csharp
string pathData = "M 100 100 L 200 200 L 100 200 Z";
SKPath path = SKPath.ParseSvgPathData(pathData);
canvas.DrawPath(path, paint);
```

## Clipping

Use paths to define which areas of the canvas are drawable.

```csharp
canvas.ClipPath(path, SKClipOperation.Intersect, true);
// Subsequent drawing is clipped to the path
```

## Paths and Text

You can draw text along a path or convert text to a path.

```csharp
canvas.DrawTextOnPath("Text along a curve", path, 0, 0, paint);

// Convert text to path for advanced effects
SKPath textPath = paint.GetTextPath("Outline", 100, 100);
canvas.DrawPath(textPath, outlinePaint);
```
