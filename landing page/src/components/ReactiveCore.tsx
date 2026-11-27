"use client";

import { useEffect, useMemo, useState } from "react";
import { Scene } from "@/components/Scene";
import { MARKETS, formatPrice, type MarketKey } from "@/lib/market";
import { FOCUS_COLOR, formatSignedPct } from "@/lib/ui";
import type { AgentStats, ConsensusView, InstrumentView, SignalView } from "@/lib/types";

type ColorMode = "desk" | "sentiment" | "pulse";

/** Desk hue (degrees) used for the reactive colour combination. */
const DESK_HUE: Record<MarketKey, number> = {
  gold: 40,
  forex: 187,
  us: 222,
  india: 152,
};

/** Base gradient the tint layer rotates through (warm gold → cyan → blue). */
const TINT_GRADIENT =
  "linear-gradient(118deg, #ffe1a0 0%, #f2c46b 26%, #7df0e6 58%, #9db9ff 100%)";

type ReactiveCoreProps = {
  instrument: InstrumentView | undefined;
  stats: AgentStats;
  consensus: ConsensusView[];
  signals: SignalView[];
  selectedMarket: MarketKey;
  onMarketChange: (market: MarketKey) => void;
  onScan: () => void;
  scanning: boolean;
  autoScan: boolean;
  onToggleAutoScan: () => void;
};

/**
 * The terminal's single reactive 3D visual.
 *
 * It renders only the uploaded ThreeUI `ConstellationField` (gateway-flow)
 * and lets the whole 550-agent swarm drive it:
 *  - density  ← share of agents active/scanning (quantised trajectories)
 *  - speed    ← live market energy (price move + signal velocity)
 *  - opacity  ← energy floor
 *  - colour   ← reactive colour combination (desk / sentiment / pulse)
 */
export function ReactiveCore({
  instrument,
  stats,
  consensus,
  signals,
  selectedMarket,
  onMarketChange,
  onScan,
  scanning,
  autoScan,
  onToggleAutoScan,
}: ReactiveCoreProps) {
  const [colorMode, setColorMode] = useState<ColorMode>("desk");
  const [pulseDeg, setPulseDeg] = useState(0);

  useEffect(() => {
    if (colorMode !== "pulse") return;
    const timer = setInterval(() => setPulseDeg((deg) => (deg + 3) % 360), 90);
    return () => clearInterval(timer);
  }, [colorMode]);

  const energy = useMemo(() => {
    const move = Math.min(1, Math.abs(instrument?.changePct ?? 0) / 0.9);
    const velocity = Math.min(1, signals.length / 16);
    return Math.min(1, move * 0.6 + velocity * 0.4);
  }, [instrument?.changePct, signals.length]);

  const speed = Number((0.55 + energy * 1.9).toFixed(2));
  const opacity = Number((0.82 + energy * 0.18).toFixed(2));

  // All agents → trajectory density. Quantised to 0.25 so the canonical
  // document only re-bakes when the swarm's activity band actually changes.
  const activeAgents = stats.active + stats.scanning;
  const activeRatio = stats.total > 0 ? activeAgents / stats.total : 0;
  const density = Math.min(2.25, Math.max(0.5, Math.round((activeRatio * 2.2) / 0.25) * 0.25));
  const trajectories = Math.round(80 * density);

  const selectedConsensus = consensus.find((item) => item.market === selectedMarket);
  const score = selectedConsensus?.score ?? 0;
  const deskColor = FOCUS_COLOR[selectedMarket] ?? "#f2c46b";
  const deskHue = DESK_HUE[selectedMarket];
  const biasHue = score > 8 ? 150 : score < -8 ? 354 : 43;
  const biasColor = score > 8 ? "#57e0a0" : score < -8 ? "#ff7d88" : "#f2c46b";
  const biasLabel = selectedConsensus?.bias.toUpperCase() ?? "NEUTRAL";

  // Colour combination: the tint gradient is hue-rotated toward the desk hue,
  // the swarm's sentiment hue, or continuously cycled in pulse mode.
  const tintRotation =
    colorMode === "desk" ? deskHue - 40 : colorMode === "sentiment" ? biasHue - 40 : pulseDeg;
  const tintLabel =
    colorMode === "desk"
      ? `${selectedMarket} desk ${deskHue}°`
      : colorMode === "sentiment"
        ? `${biasLabel.toLowerCase()} sentiment ${biasHue}°`
        : `pulse ${pulseDeg}°`;

  return (
    <div
      className="panel relative overflow-hidden rounded-xl transition-all duration-700"
      style={{ borderColor: `${deskColor}59`, boxShadow: `0 0 80px -26px ${deskColor}` }}
    >
      <div className="relative h-[460px] w-full bg-black sm:h-[540px]">
        {/* The one and only 3D visual: uploaded ThreeUI ConstellationField */}
        <Scene speed={speed} density={density} opacity={opacity} />

        {/* Reactive colour combination: multiplies the white gateway lines
            with a rotating two-tone gradient (black stage stays black). */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background: TINT_GRADIENT,
            mixBlendMode: "multiply",
            opacity: 0.92,
            filter: `hue-rotate(${tintRotation}deg) saturate(1.25)`,
            transition: "filter 0.9s ease",
          }}
        />
        {/* Sentiment glow wash */}
        <div
          className="pointer-events-none absolute inset-0 transition-all duration-700"
          style={{
            background: `radial-gradient(ellipse 62% 52% at 68% 26%, ${biasColor}2e, transparent 65%)`,
            mixBlendMode: "screen",
          }}
        />
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="animate-scan h-[16%] w-full bg-gradient-to-b from-transparent via-white/[0.04] to-transparent" />
        </div>

        {/* top overlay */}
        <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-3 p-3.5">
          <div>
            <div className="flex items-center gap-2">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan opacity-70" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-cyan" />
              </span>
              <span className="font-mono text-[9.5px] tracking-[0.22em] text-cyan uppercase">
                Reactive 3D · ConstellationField
              </span>
            </div>
            <p className="mt-1 font-mono text-[9px] tracking-[0.16em] text-muted uppercase">
              {stats.total.toLocaleString()} agents → {trajectories} trajectories · speed {speed.toFixed(2)}× ·{" "}
              <span style={{ color: deskColor }}>{tintLabel}</span>
            </p>
          </div>
          <div className="pointer-events-auto flex flex-wrap justify-end gap-1">
            {MARKETS.map((market) => (
              <button
                key={market.key}
                type="button"
                onClick={() => onMarketChange(market.key)}
                className="rounded-sm border px-1.5 py-[3px] font-mono text-[9px] tracking-[0.14em] transition-colors"
                style={{
                  color: selectedMarket === market.key ? FOCUS_COLOR[market.key] : "#7c879e",
                  borderColor: selectedMarket === market.key ? `${FOCUS_COLOR[market.key]}88` : "rgba(43,52,70,0.8)",
                  background: selectedMarket === market.key ? `${FOCUS_COLOR[market.key]}14` : "rgba(5,6,10,0.4)",
                }}
              >
                {market.short}
              </button>
            ))}
          </div>
        </div>

        <span className="pointer-events-none absolute top-3 left-3 h-4 w-4 border-t border-l" style={{ borderColor: `${deskColor}66` }} />
        <span className="pointer-events-none absolute top-3 right-3 h-4 w-4 border-t border-r" style={{ borderColor: `${deskColor}66` }} />
        <span className="pointer-events-none absolute bottom-3 left-3 h-4 w-4 border-b border-l" style={{ borderColor: `${deskColor}66` }} />
        <span className="pointer-events-none absolute right-3 bottom-3 h-4 w-4 border-r border-b" style={{ borderColor: `${deskColor}66` }} />

        {/* center readout */}
        <div className="pointer-events-none absolute inset-x-0 bottom-[86px] flex flex-col items-center text-center">
          <div className="flex items-center gap-2">
            <span className="h-px w-8 bg-gradient-to-r from-transparent" style={{ background: `linear-gradient(90deg, transparent, ${deskColor}99)` }} />
            <span className="font-mono text-[9.5px] tracking-[0.24em] uppercase" style={{ color: deskColor }}>
              {instrument ? instrument.symbol : "LOADING"}
            </span>
            <span className="h-px w-8" style={{ background: `linear-gradient(270deg, transparent, ${deskColor}99)` }} />
          </div>
          <div
            className="mt-0.5 font-mono text-2xl font-semibold tracking-tight text-gold-bright text-glow-gold sm:text-[28px]"
            style={{ color: deskColor === "#f2c46b" ? undefined : deskColor }}
          >
            {instrument ? formatPrice(instrument.price, instrument.decimals) : "—"}
          </div>
          <div className="mt-1 flex items-center gap-2 font-mono text-[10px]">
            <span style={{ color: (instrument?.changePct ?? 0) >= 0 ? "#57e0a0" : "#ff7d88" }}>
              {instrument ? formatSignedPct(instrument.changePct) : "—"}
            </span>
            <span className="text-muted">/</span>
            <span className="text-muted">{instrument?.currency}</span>
            <span className="text-muted">·</span>
            <span style={{ color: biasColor }}>{biasLabel} BIAS</span>
            <span className="text-muted">·</span>
            <span className="text-muted">{selectedConsensus?.count ?? 0} signals</span>
            <span className="text-muted">·</span>
            <span className="text-muted">click stage to pulse</span>
          </div>
        </div>

        {/* bottom HUD */}
        <div className="absolute inset-x-0 bottom-0 border-t border-line/60 bg-void/55 px-3.5 py-2.5 backdrop-blur-md">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <HudMetric label="Agents" value={stats.total.toLocaleString()} color="#f2c46b" />
            <HudMetric label="Active" value={activeAgents.toString()} color="#57e0a0" />
            <HudMetric label="Trajectories" value={trajectories.toString()} color={deskColor} />
            <HudMetric label="Energy" value={`${Math.round(energy * 100)}%`} color="#5be9e0" />
            <HudMetric label="Latency" value={`${Math.round(stats.avgLatency)}ms`} color="#8ab4ff" />
            <HudMetric label="Acc" value={`${stats.avgAccuracy.toFixed(1)}%`} color="#a79bff" />

            <div className="ml-auto flex flex-wrap items-center gap-1.5">
              <div className="flex overflow-hidden rounded-sm border border-line/80" role="group" aria-label="Colour combination mode">
                {(["desk", "sentiment", "pulse"] as ColorMode[]).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setColorMode(mode)}
                    className="px-1.5 py-1 font-mono text-[8.5px] tracking-[0.12em] uppercase transition-colors"
                    style={{
                      color: colorMode === mode ? "#05060a" : "#7c879e",
                      background: colorMode === mode ? deskColor : "rgba(255,255,255,0.03)",
                    }}
                  >
                    {mode}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={onToggleAutoScan}
                className="rounded-sm border px-1.5 py-1 font-mono text-[9px] tracking-[0.12em] uppercase transition-colors"
                style={{
                  color: autoScan ? "#57e0a0" : "#7c879e",
                  borderColor: autoScan ? "rgba(87,224,160,0.5)" : "rgba(43,52,70,0.8)",
                  background: autoScan ? "rgba(87,224,160,0.1)" : "transparent",
                }}
              >
                auto {autoScan ? "on" : "off"}
              </button>
              <button
                type="button"
                onClick={onScan}
                disabled={scanning}
                className="rounded-sm border border-gold/50 bg-gold/10 px-2 py-1 font-mono text-[9px] tracking-[0.12em] text-gold uppercase transition-colors hover:bg-gold/20 disabled:opacity-50"
              >
                {scanning ? "scanning…" : "run scan"}
              </button>
            </div>
          </div>
          <div className="mt-1.5 flex items-center gap-2">
            <span className="font-mono text-[8px] tracking-[0.14em] text-muted uppercase">vol energy</span>
            <div className="h-[3px] flex-1 overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${Math.round(energy * 100)}%`, background: `linear-gradient(90deg, ${deskColor}55, ${deskColor})` }}
              />
            </div>
            <span className="font-mono text-[8px] tracking-[0.14em] text-muted uppercase">
              tint <span style={{ color: deskColor }}>{tintLabel}</span>
            </span>
          </div>
        </div>

        <div className="pointer-events-none absolute top-1/2 left-3 hidden -translate-y-1/2 space-y-1 lg:block">
          {["AGENT-DENSITY", "FLOW-SPEED", "TINT-COMBINATION"].map((label, index) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full" style={{ background: deskColor, opacity: 1 - index * 0.25 }} />
              <span className="font-mono text-[8px] tracking-[0.18em] text-muted/80">{label}</span>
            </div>
          ))}
        </div>
        <div className="pointer-events-none absolute top-1/2 right-3 hidden -translate-y-1/2 text-right lg:block">
          <div className="font-mono text-[8px] tracking-[0.18em] text-muted/80">SOURCE</div>
          <div className="font-mono text-[10px] text-cyan/80">gateway-flow</div>
          <div className="mt-2 font-mono text-[8px] tracking-[0.18em] text-muted/80">REV</div>
          <div className="font-mono text-[10px]" style={{ color: deskColor }}>
            1920ad4f
          </div>
        </div>
      </div>
    </div>
  );
}

function HudMetric({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex items-baseline gap-1">
      <span className="font-mono text-[8.5px] tracking-[0.14em] text-muted uppercase">{label}</span>
      <span className="font-mono text-[11px] tabular-nums" style={{ color }}>
        {value}
      </span>
    </div>
  );
}
