import {
  ConnectivityGraph,
  ConstellationField as ConstellationFieldEffect,
  DefenseLines,
  GatewayFlow,
  InterfaceLines,
  ParticleDrift,
  ParticleNetwork,
  TopoField,
} from "@/shaders/neuform-isolated/NeuformBatchEffects";
import type { NeuformBatchEffectProps } from "@/shaders/neuform-isolated/NeuformBatchEffects";

/**
 * Public `ConstellationField` entry, mirroring ThreeUI's
 * `shaders/constellation-field/ConstellationField` variant router.
 *
 * The registered monolithic source (`neuform-isolated/NeuformBatchEffects.tsx`)
 * exports one component per effect, with `ConstellationField` bound to the
 * `constellation-field` effect. ThreeUI's public component adds the `variant`
 * switch on top of those exports so a single import can select any effect.
 * This file reproduces that router exactly (same eight variants, same default)
 * while keeping the registered source byte-for-byte unchanged.
 */
export const VARIANT_COMPONENTS = {
  "constellation-field": ConstellationFieldEffect,
  "particle-drift": ParticleDrift,
  "particle-network": ParticleNetwork,
  "gateway-flow": GatewayFlow,
  "connectivity-graph": ConnectivityGraph,
  "interface-lines": InterfaceLines,
  "defense-lines": DefenseLines,
  "topo-field": TopoField,
} as const;

export type ConstellationFieldVariant = keyof typeof VARIANT_COMPONENTS;

export type ConstellationFieldProps = NeuformBatchEffectProps & {
  variant?: ConstellationFieldVariant;
};

export function ConstellationField({ variant = "constellation-field", ...props }: ConstellationFieldProps) {
  const Effect = VARIANT_COMPONENTS[variant] ?? VARIANT_COMPONENTS["constellation-field"];
  return <Effect {...props} />;
}
