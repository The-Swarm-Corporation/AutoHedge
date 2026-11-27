/**
 * Type support for Vite-style `?raw` imports used by the vendored ThreeUI
 * shader sources (see tools/raw-loader.cjs for the build-time counterpart).
 */
declare module "*.html?raw" {
  const content: string;
  export default content;
}

declare module "*.css?raw" {
  const content: string;
  export default content;
}
