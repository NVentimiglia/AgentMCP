---
name: scott-plot
description: >-
  [SDK · .NET plotting] ScottPlot 5 lifecycle, Scatter vs Signal vs SignalXY,
  axes/legends, cookbooks. Use when user mentions charts, plotting, Scatter,
  SignalXY, Candlestick, Heatmap, Multiplot — not for arbitrary Skia needs (see
  `skia`).
metadata:
  skill_class: sdk
  taxonomy: dotnet-charts
  stack: dotnet
  discovers_with: ScottPlot,.NET,WPF plots,Scatter,SignalXY,cookbook,changelog charts,heatmap,candles
  integrations: ScottPlot 5.x
  pairs_with: skia
triggers:
  - ScottPlot
  - SignalXY
  - add charts to dotnet
  - save plot PNG
---

# ScottPlot 5

Docs: [scottplot.net](https://scottplot.net/) —
[Quickstart](https://scottplot.net/quickstart/console/) —
[Cookbook 5](https://scottplot.net/cookbook/5/) —
[FAQ](https://scottplot.net/faq/) —
[API](https://scottplot.net/api/5/)

Target version: `ScottPlot` 5.1.x (see `.csproj`).
Use cookbook patterns for version 5 only — not legacy ScottPlot 4 APIs.

---

## References

| Need | File |
|------|------|
| All `Plot.Add.*` overloads and return types | `references/reference.md` |
| Copy-ready patterns | `references/examples.md` |
| Cookbook chapter and recipe names | `references/cookbook-catalog.md` |

---

## Core Types

- `ScottPlot.Plot` — owns plottables, panels, axes, grids, layout.
  Renders via `SavePng` / `SaveSvg` / `GetImageBytes`.
- `plot.Add` (`PlottableAdder`) — fluent factory; most calls return
  the plottable for chaining (`Label`, `LineStyle`, colors, axes).
- `plot.Axes` (`AxisManager`) — `SetLimits`, `AutoScale`,
  `GetLimits`, `DateTimeTicksBottom()`, additional axis constructors.
- `plot.Legend` / `ShowLegend(...)` / `HideLegend()`.
- `plot.Layout` — padding and subplot arrangements;
  `ScottPlot.Multiplot` for multi-plot figures.
- `plot.Sync` — lock shared with `Render()`; acquire before mutating
  plot or datasets when using interactive controls.

---

## Scatter vs Signal vs SignalXY

| Type | Data | Use when |
|------|------|----------|
| `Scatter` | X/Y pairs, unsorted OK | Moderate counts, gaps via NaN, rich styling |
| `Signal` | Y-only, evenly spaced + `period` | Large uniformly sampled series |
| `SignalXY` | X strictly ascending, uneven | Large uneven time series |
| `SignalConst` | Same as Signal, immutable | Millions of points, interactive FPS |

Prefer `Signal` or `SignalXY` over `Scatter` whenever constraints match.

---

## Typical Server-Side Workflow

1. `var plot = new ScottPlot.Plot();`
2. `plot.Add.Signal(...)` / `SignalXY(...)` / `ScatterLine(...)` / etc.
3. `plot.Title(...)`, `plot.XLabel(...)`, `plot.YLabel(...)`
4. `plot.Axes.AutoScale()` or `SetLimits(...)`
5. `scatter.Label = "..."` then `plot.ShowLegend(...)`
6. `plot.SavePng(path, width, height)` or `GetImageBytes`

See `references/examples.md`.

---

## Plottables

Plottables render in `Plot.PlottableList` order (z-order).
Remove with `Remove`, reorder with `MoveToFront`, clear with `Clear()`.

- Series: `Scatter`, `ScatterLine`, `ScatterPoints`, `Signal`,
  `SignalConst`, `SignalXY`, `FillY`, `Function`, `ErrorBar`,
  `Line`, `Marker`, `Markers`, `LollipopPlot`, `DataLogger`,
  `DataStreamer`, `DataStreamerXY`
- Finance: `Candlestick`, `OHLC`
- Bars: `Bar`/`Bars`, `Histogram`, `Box`/`Boxes`, stacked/grouped
- Proportions: `Pie`, `Coxcomb`, `RadialGaugePlot`
- Areas: `Heatmap`, `ContourLines`, `ImageRect`, `VectorField`
- Axes-as-plottables: `PolarAxis`, `SmithChartAxis`, `Radar`, `Phasor`
- Annotations: `Annotation`, `Text`, `Tooltip`, `Callout`, `Arrow`,
  `Crosshair`, `HorizontalSpan`, `VerticalSpan`, `Bracket`
- Primitives: `Rectangle`, `Circle`, polygons, arcs, `BackgroundText`

Exact signatures: `references/reference.md`.

---

## Axes

- Default: bottom numeric X, left numeric Y.
- DateTime: use `DateTimeTicksBottom()` or store as OLE doubles.
- Multi-axis: assign `IXAxis`/`IYAxis` per plottable where supported.
- Inverted axes, square units, multiplier notation: see cookbook.

---

## Pre-Ship Checklist

- [ ] Use `Signal`/`SignalXY` when data satisfies spacing constraints.
- [ ] Set `Label` on all series shown in legends; call `ShowLegend`.
- [ ] Assign correct axis types (`DateTimeTicksBottom`, right axis).
- [ ] Account for `ScaleFactor` if targeting HiDPI or social cards.
- [ ] Wrap concurrent mutations in `lock (plot.Sync)`.
