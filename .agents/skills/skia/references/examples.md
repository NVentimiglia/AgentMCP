# Skia examples (official)

Curated pointers to **official** runnable samples and embedding code—not copies of upstream source. Prefer these over random blog snippets when validating API behavior.

---

## Skia Fiddle (C++, in-browser)

[Skia Fiddle](https://fiddle.skia.org/) is linked from the [Documentation hub](https://skia.org/docs/). The docs **showcase** table highlights these named fiddles (good first clicks):

| Topic | Named fiddle |
|------|----------------|
| Basic shapes | [@shapes](https://fiddle.skia.org/c/@shapes) |
| Bézier curves | [@bezier_curves](https://fiddle.skia.org/c/@bezier_curves) |
| Transforms | [@rotations](https://fiddle.skia.org/c/@rotations) |
| Text | [@text_rendering](https://fiddle.skia.org/c/@text_rendering) |
| Discrete path effects | [@discrete_path](https://fiddle.skia.org/c/@discrete_path) |
| Composed path effects | [@compose_path](https://fiddle.skia.org/c/@compose_path) |
| Sum path effects | [@sum_path_effect](https://fiddle.skia.org/c/@sum_path_effect) |
| Shaders (intro) | [@shader](https://fiddle.skia.org/c/@shader) |

**API lookup:** hundreds of small examples are listed on [Named Fiddles](https://fiddle.skia.org/named/). Useful starting names include:

- [@BlendModes](https://fiddle.skia.org/c/@BlendModes), [@GradientShader_MakeLinear](https://fiddle.skia.org/c/@GradientShader_MakeLinear)
- [@Canvas_clipRect](https://fiddle.skia.org/c/@Canvas_clipRect), [@Canvas_saveLayer](https://fiddle.skia.org/c/@Canvas_saveLayer) (search the named list for `Canvas_` if you need a specific call)
- [@PDF](https://fiddle.skia.org/c/@PDF) — minimal PDF-related fiddle entry point
- SkSL / runtime effects in fiddle form: e.g. [@SkSL_Uniforms](https://fiddle.skia.org/c/@SkSL_Uniforms), [@SkSL_PremultipliedAlpha](https://fiddle.skia.org/c/@SkSL_PremultipliedAlpha) (see `SkSL_*` and `Shader_*` rows on the named list)

---

## SkCanvas backends (copy-paste from docs)

[SkCanvas Creation](https://skia.org/docs/user/api/skcanvas_creation) walks through **raster**, **GPU (GL)**, **SkPDF**, **SkPicture**, **NullCanvas**, and experimental **SkSVG** with full C++ snippets—use this when wiring a real app, not only fiddles.

---

## SkSL and runtime effects

- Prose + pipeline context: [SkSL & Runtime Effects](https://skia.org/docs/user/sksl/)
- Live experiments: [shaders.skia.org](https://shaders.skia.org/) (linked from that page)
- Fiddle index: filter [Named Fiddles](https://fiddle.skia.org/named/) for `SkSL_`

---

## CanvasKit (Skia + WebAssembly)

Module page: [CanvasKit](https://skia.org/docs/user/modules/canvaskit/) — includes **CanvasKit JSFiddle** samples (paragraph shaping, custom shaders, 3D cube, Lottie/Skottie fiddles, “Star”, “Ink”, etc.) and the generic [CanvasKit Fiddle](https://jsfiddle.skia.org/canvaskit).

Package / types: [canvaskit-wasm on npm](https://www.npmjs.com/package/canvaskit-wasm); types live under `types/` in the package or [Skia repo `modules/canvaskit/npm_build/types`](https://github.com/google/skia/tree/main/modules/canvaskit/npm_build/types).

---

## Skottie (Lottie)

- Browser player: [skottie.skia.org](https://skottie.skia.org/)
- Overview + embedding pointers: [Skottie module](https://skia.org/docs/user/modules/skottie/) — links to **`Skottie.h`**, **[`SkottieTool.cpp`](https://github.com/google/skia/blob/main/modules/skottie/src/SkottieTool.cpp)** sample, **[Android sample app tree](https://github.com/google/skia/tree/main/platform_tools/android/apps/skottie)**, and **[Viewer slide](https://github.com/google/skia/blob/main/tools/viewer/SkottieSlide.cpp)**

---

## Desktop Viewer (many interactive slides)

[Skia Viewer](https://skia.org/docs/user/sample/viewer) — build with GN/ninja (`viewer`), load resources/`--skps`, compare raster vs GL vs Vulkan (`--backend`). Use when you need interactive debugging beyond fiddles.

---

## Coordinate and color docs (no single “example”, but prerequisite)

- [Skia Coordinate Spaces](https://skia.org/docs/user/coordinates) (linked from SkSL page)
- [Skia Color Management](https://skia.org/docs/user/color) — ties into SkSL `layout(color)` and working color space discussion in [SkSL & Runtime Effects](https://skia.org/docs/user/sksl/)
