# Asset register

Every image, font and icon used by the website, with its source and licence (PRD DR-3).

## Images

The images are edited photos from Pexels and Unsplash and one edited illustration from Pixabay. The [Pexels licence](https://www.pexels.com/license/), the [Unsplash licence](https://unsplash.com/license) and the [Pixabay Content License](https://pixabay.com/service/license-summary/) allow free use and editing and do not require credit.

They are in `.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/mockups/images/` and move to `frontend/public/` when the frontend is built.

| File | Used on | Source and licence | Alt text |
|---|---|---|---|
| `band-loyly-steam.jpg` | Landing, band | ["Relaxing in a Steamy Modern Sauna"](https://www.pexels.com/photo/relaxing-in-a-steamy-modern-sauna-31092896/) by HUUM │sauna heaters, Pexels licence, cropped to the steam so that the person and the heater are left out, colours and contrast adjusted to match the sauna photos | Soft clouds of warm, brown-tinted steam drifting across the frame. |
| `sauna-rauha-door.jpg` | Landing, Rauha | ["Modern Indoor Sauna with Wooden Panels"](https://www.pexels.com/photo/modern-indoor-sauna-with-wooden-panels-36420270/) by HUUM │sauna heaters, Pexels licence, cropped, brand tag on the stove retouched out, colours and contrast adjusted to match the other sauna photos | A glass sauna door with a long pale wooden handle, and a stove filled with grey stones seen through it. |
| `sauna-kajo-kiulu.jpg` | Landing, Kajo | ["Modern Indoor Sauna with Wooden Panels"](https://www.pexels.com/photo/modern-indoor-sauna-with-wooden-panels-36420272/) by HUUM │sauna heaters, Pexels licence, cropped, brand name on the bucket retouched out, soft warm glow added | A black sauna bucket with a curved wooden handle and a wooden-handled ladle, on a pale wooden bench. |
| `sauna-loyly-kiuas.jpg` | Landing, Löyly | [Pixabay illustration 9176885 ("sauna, steam, relaxation, wellness")](https://pixabay.com/illustrations/sauna-steam-relaxation-wellness-9176885/) by tylijura, Pixabay Content License, cropped from portrait to landscape, colours and contrast adjusted to match the other sauna photos | Steam drifting through a softly lit wooden sauna, above dark stones heaped in a square stove, with a pale bench to the right. |
| `sauna-lumo-lauteet.jpg` | Landing, Lumo | ["Modern Nordic Sauna Interior with Wooden Design"](https://www.pexels.com/photo/modern-nordic-sauna-interior-with-wooden-design-36077597/) by HUUM │sauna heaters, Pexels licence, cropped to the benches so that the heater and its brand name are left out, colours and contrast adjusted to match the other sauna photos | Empty wooden sauna benches along a wall, lit softly from behind the backrest. |
| `hero-sauna-by-the-water.jpg` | Landing, hero | ["Oslo badsteforening sauna at sunset"](https://unsplash.com/photos/DusOaeCX_ss) by Eirik Skarstein, Unsplash licence, cropped to landscape, the organisation's logo and name, the SAUNA sign, a sign on a building, a sticker, a notice, a life buoy, two poles, a tall building with its reflection, the crane and buildings behind the railing, a far building, the roof beam at the left with the structure under it, the mesh and fittings on the railing, the buildings on the far shore with their reflections and a lens flare retouched out, the side panel, railing, sky and sea extended where the beam stood, wall boards rebuilt from a clean part of the photo, sun's glow and its light on the water reworked, colours and contrast adjusted to match the sauna photos | A dark wooden sauna with a railing on its roof, standing in calm water, with the low sun glowing softly over the open sea and golden light on the surface. |
| `before-towels.jpg` | Landing, Before you come | ["Brown Bottle on Towels"](https://www.pexels.com/photo/brown-bottle-on-towels-7795756/) by Alesia Kozik, Pexels licence, rotated and cropped so that the bottle is left out, colours and contrast adjusted to match the sauna photos | A rolled grey towel beside a beige towel in a cork tray. |

## Fonts

Both fonts are self-hosted in `frontend/public/fonts/` and loaded through `@font-face` in `frontend/app/styles.css`, so no font is requested from another origin (FR-21). They come from [`github.com/google/fonts`](https://github.com/google/fonts) under the [SIL Open Font License 1.1](https://openfontlicense.org/), which allows use, embedding and redistribution with the licence. Each variable font was converted once from `.ttf` to `.woff2` with fonttools, without subsetting, so every glyph and feature of the source is kept: both have ö, Finlandica has `tnum`, and Source Sans 3's default figures are already tabular (all ten digits are equally wide). The licence texts are in `frontend/font-licenses/`.

| File | Used on | Source and licence | Notes |
|---|---|---|---|
| `fonts/finlandica-variable.woff2` | Every page: headings and the Wordmark | [`ofl/finlandica/Finlandica[wght].ttf`](https://github.com/google/fonts/tree/main/ofl/finlandica) (google/fonts commit `a60a77e`), Finlandica 1.064, © 2015 The Finlandica Project Authors, SIL OFL 1.1 ([`OFL-Finlandica.txt`](frontend/font-licenses/OFL-Finlandica.txt)) | Variable weight 400–700. SHA-256 `097c7b41…3b6f` |
| `fonts/source-sans-3-variable.woff2` | Every page: all text | [`ofl/sourcesans3/SourceSans3[wght].ttf`](https://github.com/google/fonts/tree/main/ofl/sourcesans3) (google/fonts commit `914ec11`), Source Sans 3 3.052, © 2010–2020 Adobe, with Reserved Font Name "Source", SIL OFL 1.1 ([`OFL-SourceSans3.txt`](frontend/font-licenses/OFL-SourceSans3.txt)) | Variable weight 200–900, upright only. SHA-256 `f336c96e…dccb` |

## Known exception

The Venue name "Saunalöyly" is kept although other parties hold marks for "Löyly", because the Venue is fictional and not used in trade (PRD §12 Q10).
