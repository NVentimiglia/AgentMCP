# ScottPlot 5 reference (Plot + AxisManager + `plot.Add`)

Authoritative dumps: **[ScottPlot 5 API browser](https://scottplot.net/api/5/)** (types and members regenerate with each release). GammaCharts pins **`ScottPlot` 5.1.x** NuGet ([quickstart index](https://scottplot.net/), [FAQ](https://scottplot.net/faq/)).

Conceptual FAQs: Scatter vs Signal is explained on [ScottPlot FAQ](https://scottplot.net/faq/) (“Scatter Plot vs Signal Plot”).

---

## `ScottPlot.Plot`

Key members (abbreviated):

| Area | Typical members |
|------|----------------|
| Compose | **`Add`** → **`ScottPlot.PlottableAdder`** |
| Axes grid | **`Axes`** → **`AxisManager`** (limits, autoscaler, margins, ticks, grids) |
| Layout | **`Layout`** → **`LayoutManager`** |
| Visual chrome | **`Title`**, **`XLabel`**, **`YLabel`**, **`ShowLegend`** / **`HideLegend`**, **`Legend`** panel |
| Styling | **`Style`**, **`FigureBackground`**, **`DataBackground`**, **`FigureBorder`**, **`DataBorder`**, **`Grid`**, **`Font`**, **`ScaleFactor`** |
| State | **`PlottableList`**, **`GetPlottables()`**, **`Clear()`**, **`Remove(...)`**, **`MoveToFront`/`Back`** |
| Threading | **`Sync`** lock object coordinating with **`Render`** |
| Raster / file | **`Render`**, **`GetImage`**, **`Save`**, **`SavePng`**, **`SaveSvg`**, **`SaveJpeg`**, **`SaveWebp`**, **`SaveBmp`**, **`GetImageBytes`**, **`GetSvgXml`**, HTML helpers |
| Coords | **`GetPixel`**, **`GetCoordinates`**, **`GetCoordinateRect`** |

---

## `Plot.Axes` (`AxisManager`) — common calls

- **Limits**: `SetLimits`, `SetLimitsX`, `SetLimitsY`, overloads incl. **`AxisLimits`** + specific **`IXAxis`/`IYAxis`**
- **Read bounds**: **`GetLimits`**, **`GetDataLimits`**, **`LimitsHaveBeenSet`**
- **Auto**: **`AutoScale`**, **`AutoScaleExpand`**, **`ContinuouslyAutoscale`**, **`ContinuousAutoscaleAction`**
- **Direction**: **`InvertX`/`RectifyX`**, **`InvertY`/`RectifyY`**
- **Axis instances**: **`Bottom`**, **`Left`**, **`Right`**, **`Top`**, **`GetAxes()`**, **`AddLeftAxis`** / **`AddRightAxis`** / **`AddBottomAxis`** / **`AddTopAxis`**
- **Conveniences**: **`DateTimeTicksBottom()`**, **`NumericTicksBottom()`**
- **Grids**: **`DefaultGrid`**, **`CustomGrids`**, **`AllGrids`**, etc.
- **Rules**: **`Rules`** (axis rules incl. square units)
- **Panels**: **`Title`**, panels API via **`IPanel`** list operations

Consult API page for exhaustive signatures parameter lists.

---

## `Plot.Add` (`PlottableAdder`)

Factory for **`IPlottable`** instances attached to **`Plot`**. Signature list below distilled from **`ScottPlot` 5.1.58** generated API docs (minor upstream drift vs 5.1.57 NuGet is expected).

**Palette / sequencing**

- **`IPalette Palette`**, **`Plot Plot`**, **`Color GetNextColor(bool incrementCounter)`**

**Shapes / ellipse family**

- `AnnularEllipticalSector(...)` overloads (`Coordinates`, `Angles`, radii)
- `AnnularSector(...)`
- `Arc(...)`, **`Circle`**, **`CircleSector`**, **`Ellipse`**, **`EllipticalArc`**, **`EllipticalSector`**

**Markers / primitives**

- **`Arrow`** (coordinate pairs / **`CoordinateLine`**)
- **`Bar`**, **`Bars`** overloads (**`Bar`**, arrays, **`IEnumerable`** positions + values)
- **`Box`**, **`Boxes`**
- **`Bracket`**
- **`Callout`**
- **`Candlestick`**, **`OHLC`**
- **`BackgroundText`** (string + multiline **`ValueTuple`**)

**Panels specialized**

- **`ColorBar`** (from **`IHasColorAxis`** + **`Edge`**)

**Data continuous / fields**

- **`ContourLines`** (2D **`Coordinates3d`** grid or array + level count)
- **`Coxcomb`**
- **`Crosshair`**
- **`DataLogger`**, **`DataStreamer`**, **`DataStreamerXY`**
- **`ErrorBar`**
- **`FillY`** (arrays, between two **`Scatter`**, generic collections + converter)
- **`Function`** (**`IFunctionSource`** or **`Func<double, double>`**)
- **`Heatmap`** (`double[,]` or **`Coordinates3d[,]`**)
- **`Histogram`**
- **`HorizontalLine`**, **`VerticalLine`**
- **`HorizontalSpan`**, **`VerticalSpan`**
- **`InteractiveHorizontalLine`** / **`VerticalLine`** / **`LineSegment`** / **`Span`** / **`Marker`** / **`Rectangle`**

**Art / overlays**

- **`ImageMarker`**, **`ImageRect`**
- **`Line`** (**`CoordinateLine`** / coordinates)
- **`Lollipop`** (values / positions / coordinates)
- **`Marker`**, **`Markers`** (double/coordinate sequences + **`MarkerShape`**)
- **`Phasor`**
- **`Pie`**
- **`Plottable(IPlottable)`** manual add
- **`PolarAxis`**
- **`Polygon`**
- **`Population`**
- **`Radar`**
- **`RadialGaugePlot`**
- **`Ranges`**, **`StackedRanges`** (range collections + palette)
- **`Rectangle`**

**Optimized series**

- **`Scatter`** / **`ScatterLine`** / **`ScatterPoints`** — **`IScatterSource`**, arrays, **`Coordinates`**, generic lists **`T[], T`** pairs
- **`Signal`** (**`ISignalSource`**, double period, generics, **`IReadOnlyList`**, **`SignalConst`**)
- **`SignalXY`** (**`ISignalXYSource`**, array pairs, lists)
- **`SmithChartAxis`**
- **`ScaleBar`**

**Annotations**

- **`Annotation`**, **`Text`**, **`Tooltip`**, **`Legend()`**
- **`TriangularAxis`**
- **`VectorField`**

Upstream may add/remove overloads; cross-check IntelliSense against [API index](https://scottplot.net/api/5/) when compiling.
