# ThreeUI shader sources (vendored)

These files are the **registered source** for ThreeUI's `ConstellationField`
component, `gateway-flow` variant. They are vendored verbatim so the terminal
does not depend on a published bundle.

## Provenance

Bundle: <https://threeui.com/source-code/gateway-flow.json> (`schemaVersion: 1`,
`id: gateway-flow`). Every file below matched its registered SHA-256 on install.

| File | Role | SHA-256 |
| --- | --- | --- |
| `neuform-isolated/NeuformBatchEffects.tsx` | component | `dc68c51bea26b922965de44b4fb8d6c432607508fb2b61e16ed60d245da1a69f` |
| `neuform-isolated/sources/gateway-flow.html` | canonical-source | `c5a1de43138ffba96b9f0ecdcf3c054ae251ec94344e88c6ad502bae362b17d0` |
| `threeui.css` | shared-style | `efe4447139f1358dd8e9be68edf6fa46cbefbd1de423a4d6c439ca61d2c8eccf` |

`neuform-isolated/sources/*.html` — the component statically imports all 18
canonical documents, so the sibling documents shipped in the same ThreeUI
revision are vendored alongside `gateway-flow.html`. As a revision check,
`sources/constellation-field.html` hashes to `1920ad4fe34f…`, the source
revision quoted for this integration.

`fonts/fragment-mono.woff2` — `threeui.css` authors
`url("./fonts/fragment-mono.woff2")`; the binary is not published in the bundle
or the npm tarball, so the genuine OFL-licensed Fragment Mono latin subset from
Google Fonts is placed at the authored path.

## Integration notes

- The component streams its canonical document into
  `<iframe sandbox="allow-scripts" srcDoc={…}>` and drives it through
  `postMessage` (`threeui-controls`). Focus CSS hides everything except the
  `#flow-canvas` layer, which becomes the full-bleed black stage.
- The authored document depends on four CDN scripts (Tailwind, Iconify, GSAP,
  ScrollTrigger). The canvas animation lives inside the same
  `DOMContentLoaded` handler as the GSAP reveal, so those scripts must load for
  the trajectories to start. This is authored behaviour and is preserved.
- `?raw` imports are Vite syntax; `tools/raw-loader.cjs` plus the `turbopack`
  rule in `next.config.ts` reproduce it byte-for-byte (no transformation).
- The registered monolith binds `ConstellationField` to the
  `constellation-field` effect directly. ThreeUI's public entry adds the
  `variant` switch on top of the per-effect exports, so
  `constellation-field/ConstellationField.tsx` mirrors that router, leaving this
  registered component untouched.
