"use client";

import { PanelHeader } from "@/components/ui";
import { FOCUS_COLOR, focusLabel } from "@/lib/ui";
import { MARKETS, type MarketKey } from "@/lib/market";
import type { AgentStats, ConsensusView } from "@/lib/types";

export function ConsensusBoard({
  consensus,
  stats,
  focus,
}: {
  consensus: ConsensusView[];
  stats: AgentStats;
  focus: string;
}) {
  const overall =
    consensus.length > 0 ? Math.round(consensus.reduce((sum, item) => sum + item.score, 0) / consensus.length) : 0;
  const totalSignals = consensus.reduce((sum, item) => sum + item.count, 0);
  const deskBias = overall > 8 ? "risk-on long" : overall < -8 ? "risk-off short" : "neutral / two-way";

  return (
    <div className="panel flex flex-col overflow-hidden rounded-xl">
      <PanelHeader
        title="Swarm Consensus"
        subtitle={`${totalSignals} live signals`}
        accent="#5be9e0"
        right={
          <span
            className="rounded-sm border px-1.5 py-[2px] font-mono text-[9px] tracking-[0.12em] uppercase"
            style={{
              color: overall >= 0 ? "#57e0a0" : "#ff7d88",
              borderColor: overall >= 0 ? "rgba(87,224,160,0.4)" : "rgba(255,125,136,0.4)",
            }}
          >
            net {overall > 0 ? "+" : ""}
            {overall}
          </span>
        }
      />

      <div className="divide-y divide-line/50">
        {MARKETS.map((market) => {
          const view = consensus.find((item) => item.market === market.key);
          const accent = FOCUS_COLOR[market.key];
          const total = view ? Math.max(1, view.bullish + view.bearish + view.neutral) : 1;
          return (
            <div key={market.key} className="px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[9.5px] tracking-[0.14em]" style={{ color: accent }}>
                    {market.short}
                  </span>
                  <span className="font-mono text-[8.5px] text-muted/80">{view?.label ?? market.label}</span>
                </div>
                <div className="flex items-center gap-1.5 font-mono text-[9px]">
                  <span className="text-mint">{view?.bullish ?? 0}</span>
                  <span className="text-muted/50">/</span>
                  <span className="text-rose">{view?.bearish ?? 0}</span>
                  <span className="text-muted/50">/</span>
                  <span className="text-gold">{view?.neutral ?? 0}</span>
                </div>
              </div>
              <div className="mt-1 flex h-[5px] w-full overflow-hidden rounded-full bg-white/[0.05]">
                <div
                  className="h-full transition-all duration-700"
                  style={{ width: `${((view?.bullish ?? 0) / total) * 100}%`, background: "linear-gradient(90deg,#2f9c72,#57e0a0)" }}
                />
                <div
                  className="h-full transition-all duration-700"
                  style={{ width: `${((view?.neutral ?? 0) / total) * 100}%`, background: "linear-gradient(90deg,#8a7038,#f2c46b)" }}
                />
                <div
                  className="h-full transition-all duration-700"
                  style={{ width: `${((view?.bearish ?? 0) / total) * 100}%`, background: "linear-gradient(90deg,#a24a52,#ff7d88)" }}
                />
              </div>
              <div className="mt-1 flex items-center justify-between font-mono text-[8px] tracking-[0.08em] text-muted/70 uppercase">
                <span className="truncate">lead · {view?.leadAgent ?? "awaiting quorum"}</span>
                <span style={{ color: view?.bias === "long" ? "#57e0a0" : view?.bias === "short" ? "#ff7d88" : "#f2c46b" }}>
                  {view?.bias ?? "neutral"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-line/70 bg-black/20 px-3 py-2.5">
        <div className="flex items-center justify-between">
          <span className="label">Desk posture</span>
          <span className="font-mono text-[10px] tracking-[0.1em] text-gold uppercase">{deskBias}</span>
        </div>
        <div className="mt-2 grid grid-cols-3 gap-2">
          <MiniStat label="Models" value={(stats.byFocus.length + 11).toString()} />
          <MiniStat label="Avg acc" value={`${stats.avgAccuracy.toFixed(1)}%`} />
          <MiniStat label="P&L Σ" value={`${stats.aggregatePnl > 0 ? "+" : ""}${Math.round(stats.aggregatePnl).toLocaleString()}`} />
        </div>
        <div className="mt-2 flex flex-wrap gap-1">
          {stats.byFocus
            .filter((row) => row.focus !== "macro")
            .sort((a, b) => b.count - a.count)
            .map((row) => (
              <span
                key={row.focus}
                className="rounded-sm border px-1.5 py-[2px] font-mono text-[8px] tracking-[0.1em]"
                style={{
                  color: FOCUS_COLOR[row.focus] ?? "#7c879e",
                  borderColor: `${FOCUS_COLOR[row.focus] ?? "#7c879e"}33`,
                }}
              >
                {focusLabel(row.focus as MarketKey | "macro")} {row.count}
              </span>
            ))}
        </div>
        <div className="mt-2 flex items-center justify-between border-t border-line/50 pt-2">
          <span className="label">Viewing</span>
          <span className="font-mono text-[9px] tracking-[0.14em] text-cyan uppercase">{focus} desk</span>
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-sm border border-line/60 bg-white/[0.02] px-1.5 py-1">
      <div className="font-mono text-[7.5px] tracking-[0.12em] text-muted/80 uppercase">{label}</div>
      <div className="truncate font-mono text-[10px] tabular-nums text-ink/90">{value}</div>
    </div>
  );
}
