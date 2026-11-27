"use client";

import type { AgentStats, AgentView, SignalView } from "@/lib/types";
import { FOCUS_COLOR } from "@/lib/ui";

export function CoreTelemetry({
  stats,
  leaderboard,
  signals,
  onOpenAgent,
}: {
  stats: AgentStats;
  leaderboard: AgentView[];
  signals: SignalView[];
  onOpenAgent: (id: number) => void;
}) {
  const bullish = signals.filter((signal) => signal.direction === "bullish").length;
  const ratio = signals.length > 0 ? Math.round((bullish / signals.length) * 100) : 50;

  return (
    <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
      <Tile
        label="Agents online"
        value={stats.total.toLocaleString()}
        hint={`${stats.active + stats.scanning} active · ${stats.riskHold} risk-hold`}
        accent="#f2c46b"
      />
      <Tile
        label="Desk throughput"
        value={(stats.totalSignals / 1000).toFixed(1) + "k"}
        hint={`${Math.round(stats.avgLatency)}ms avg inference`}
        accent="#5be9e0"
      />
      <Tile
        label="Bull / bear skew"
        value={`${ratio}% / ${100 - ratio}%`}
        hint={`${signals.length} signals in window`}
        accent="#a79bff"
        bar={ratio}
      />
      <div className="panel rounded-lg px-2.5 py-2">
        <div className="flex items-center justify-between">
          <span className="label">Alpha leaders</span>
          <span className="font-mono text-[8px] tracking-[0.1em] text-gold/70 uppercase">acc</span>
        </div>
        <div className="mt-1 space-y-1">
          {leaderboard.slice(0, 3).map((agent, index) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => onOpenAgent(agent.id)}
              className="flex w-full items-center gap-1.5 text-left"
            >
              <span className="font-mono text-[8px] text-muted/70">0{index + 1}</span>
              <span
                className="h-1 w-1 shrink-0 rounded-full"
                style={{ background: FOCUS_COLOR[agent.focus] ?? "#7c879e" }}
              />
              <span className="truncate font-mono text-[9px] text-ink/75 hover:text-gold">{agent.codename}</span>
              <span className="ml-auto font-mono text-[9px] tabular-nums text-mint/80">{agent.accuracy.toFixed(1)}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Tile({
  label,
  value,
  hint,
  accent,
  bar,
}: {
  label: string;
  value: string;
  hint: string;
  accent: string;
  bar?: number;
}) {
  return (
    <div className="panel relative overflow-hidden rounded-lg px-2.5 py-2">
      <span className="absolute inset-x-0 top-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${accent}88, transparent)` }} />
      <div className="flex items-center justify-between">
        <span className="label">{label}</span>
        <span className="h-1 w-1 rounded-full" style={{ background: accent, boxShadow: `0 0 6px ${accent}` }} />
      </div>
      <div className="mt-0.5 font-mono text-[16px] font-semibold tabular-nums" style={{ color: accent }}>
        {value}
      </div>
      <div className="truncate font-mono text-[8px] tracking-[0.08em] text-muted/80 uppercase">{hint}</div>
      {typeof bar === "number" ? (
        <div className="mt-1 flex h-[2px] w-full overflow-hidden rounded-full bg-white/[0.06]">
          <div className="h-full" style={{ width: `${bar}%`, background: "#57e0a0" }} />
          <div className="h-full flex-1" style={{ background: "#ff7d88" }} />
        </div>
      ) : null}
    </div>
  );
}
