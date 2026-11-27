/**
 * Webpack/Turbopack-compatible raw source loader.
 *
 * The registered ThreeUI batch-effect component imports its canonical HTML
 * sources with Vite's `?raw` suffix, e.g.
 *
 *   import gatewayFlowSource from "./sources/gateway-flow.html?raw";
 *
 * Next.js has no native `?raw` support, so this loader reproduces Vite's
 * behaviour exactly: it emits the untouched file contents as a default export
 * string. Nothing is parsed, transformed, or minified.
 */
module.exports = function threeuiRawLoader(source) {
  return `export default ${JSON.stringify(source)};`;
};
