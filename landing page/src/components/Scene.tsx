import { ConstellationField } from "@/shaders/constellation-field/ConstellationField";
import "@/shaders/threeui.css";

export type SceneProps = {
  className?: string;
  /**
   * Optional live overrides. All default to the configured usage values below,
   * so `<Scene />` renders the registered preset exactly.
   */
  speed?: number;
  size?: number;
  length?: number;
  density?: number;
  opacity?: number;
  hue?: number;
  saturation?: number;
  brightness?: number;
};

/**
 * Gateway Flow scene.
 *
 * Renders the registered ThreeUI `ConstellationField` (variant `gateway-flow`)
 * from `src/shaders/neuform-isolated/NeuformBatchEffects.tsx`, which streams the
 * canonical `sources/gateway-flow.html` document into a sandboxed iframe and
 * drives it through postMessage controls.
 */
export function Scene({
  className,
  speed = 1.0,
  size = 1.0,
  length = 1.0,
  density = 1.0,
  opacity = 1.0,
  hue = 0,
  saturation = 1.0,
  brightness = 1.0,
}: SceneProps) {
  return (
    <div className={`shader-frame ${className ?? ""}`.trim()}>
      <ConstellationField
        variant="gateway-flow"
        mode="dark"
        speed={speed}
        size={size}
        length={length}
        density={density}
        opacity={opacity}
        hue={hue}
        saturation={saturation}
        brightness={brightness}
      />
    </div>
  );
}
