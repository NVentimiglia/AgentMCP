# ScottPlot 5 examples (minimal + common paths)

Companion to [SKILL.md](../SKILL.md). For exhaustive recipes, open named links in [cookbook-catalog.md](cookbook-catalog.md) or browse [ScottPlot 5 cookbook](https://scottplot.net/cookbook/5/). Generated API surface: [scottplot.net/api/5](https://scottplot.net/api/5/).

---

## Console quicksave (scatter)

From [Console quickstart](https://scottplot.net/quickstart/console/):

```csharp
double[] dataX = { 1, 2, 3, 4, 5 };
double[] dataY = { 1, 4, 9, 16, 25 };

ScottPlot.Plot plot = new();
plot.Add.Scatter(dataX, dataY);
plot.SavePng("quickstart.png", 400, 300);
```

---

## Signal vs Scatter (prefer Signal when spaced)

Uniform sampling — use **`Add.Signal`** with **`period`** (Δx):

```csharp
using System.Linq;

double[] ys = Enumerable.Range(0, 500).Select(i => Math.Sin(i * 0.05)).ToArray();
ScottPlot.Plot plot = new();
plot.Add.Signal(ys, period: 0.05);
plot.Axes.AutoScale();
plot.Title("Waveform");
plot.XLabel("Time");
plot.SavePng("signal.png", 800, 400);
```

Non-uniform or unsorted — **`Add.ScatterLine`** / **`ScatterPoints`** / **`Scatter`**.

Cookbook: [Scatter](https://scottplot.net/cookbook/5/Scatter), [Signal](https://scottplot.net/cookbook/5/Signal).

---

## SignalXY (ascending X)

```csharp
using System.Linq;

double[] xs = Enumerable.Range(0, 800).Select(i => i * 0.015).ToArray();
double[] ys = Enumerable.Range(0, xs.Length).Select(i => xs[i] * xs[i] * 1e-3 + Math.Sin(i * 0.02)).ToArray();

ScottPlot.Plot plot = new();
plot.Add.SignalXY(xs, ys);
plot.Axes.AutoScale();
plot.SavePng("signalxy.png", 800, 400);
```

Cookbook: [SignalXY](https://scottplot.net/cookbook/5/SignalXY).

---

## Legend + labels + autoscale return value

Most `plot.Add.*` calls return the plottable; set **`Label`**, **`LineWidth`**, etc.

```csharp
using System.Linq;

double[] xs = Enumerable.Range(0, 50).Select(i => i * 1.0).ToArray();
double[] ys1 = xs.Select(Math.Sin).ToArray();
double[] ys2 = xs.Select(Math.Cos).ToArray();

ScottPlot.Plot plot = new();
var s1 = plot.Add.ScatterLine(xs, ys1);
s1.Label = "Series A";
var s2 = plot.Add.ScatterLine(xs, ys2);
s2.LineWidth = 2;
s2.Label = "Series B";

plot.Title("Legend demo");
plot.XLabel("X");
plot.YLabel("Y");
plot.ShowLegend();
plot.Axes.AutoScale();
plot.SavePng("legend.png", 600, 400);
```

---

## DateTime bottom axis helper

Cookbook guides `DateTime.ToOADate()` / OLE doubles — or replace bottom axis via **`Axes`**:

```csharp
plot.Axes.DateTimeTicksBottom();
// plot coordinates as double from DateTime conversions
```

See [Axis and ticks](https://scottplot.net/cookbook/5/AxisAndTicks).

---

## Candlesticks (financial)

Uses **`ScottPlot.OHLC`** payloads — see cookbook for full SMA/Bollinger patterns.

```csharp
ScottPlot.OHLC[] candles = {/* ... populate from bars ... */};
ScottPlot.Plot plot = new();
plot.Add.Candlestick(candles);
plot.Axes.AutoScale();
plot.SavePng("finance.png", 900, 500);
```

Cookbook: [Finance](https://scottplot.net/cookbook/5/Finance).

---

## Heatmap skeleton

```csharp
double[,] data = {/* rows × cols */ };
ScottPlot.Plot plot = new();
plot.Add.Heatmap(data);
plot.SavePng("heatmap.png", 600, 400);
```

Cookbook: [Heatmap](https://scottplot.net/cookbook/5/Heatmap).

---

## Threading / mutate under render lock

ScottPlot warns when UI or threads mutate **`Plot`** or backing arrays concurrently. Coordinate with **`plot.Sync`** and/or host control patterns — see FAQ [locking in multi-threaded/async environments](https://scottplot.net/faq/).

```csharp
lock (plot.Sync)
{
    plot.PlottableList.Clear();
    plot.Add.Scatter(xs, ys);
    plot.Axes.AutoScale();
}
```

(Host apps often schedule updates on UI thread instead — follow platform guidance.)

---

## Export helpers (server / API)

Beyond **`SavePng`**: **`SaveSvg`**, **`SaveWebp`**, **`SaveJpeg`**, **`SaveBmp`**, **`GetImageBytes`**, **`GetImageHtml`**. See **`ScottPlot.ImageFormat`** overloads on **`Plot`** in [generated API](https://scottplot.net/api/5/).
