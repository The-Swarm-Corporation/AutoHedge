"use client";

import { useMemo, useState } from "react";
import { Chip, DirectionPill, Meter, PanelHeader } from "@/components/ui";
import { FOCUS_COLOR, formatUtcClock } from "@/lib/ui";
import { MARKETS, formatPrice, type MarketKey } from "@/lib/market";
import type { SignalView } from "@/lib/types";

export function SignalFeed({
  signals,
  onOpenAgent,
  onScan,
  scanning,
  autoScan,
  onToggleAutoScan,
}: {
  signals: SignalView[];
  onOpenAgent: (id: number) => void;
  onScan: () => void;
  scanning: boolean;
  autoScan: boolean;
  onToggleAutoScan: () => void;
}) {
  const [filter, setFilter] = useState<"all" | MarketKey>("all");
  const visible = useMemo(
    () => (filter === "all" ? signals : signals.filter((signal) => signal.market === filter)),
    [filter, signals],
  );

  return (
    <div className="panel flex h-[540px] flex-col overflow-hidden rounded-xl">
      <PanelHeader
        title="Live Agent Signals"
        subtitle={`${signals.length} in feed`}
        accent="#a79bff"
        right={
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={onToggleAutoScan}
              className="rounded-sm border px-1.5 py-[2px] font-mono text-[8.5px] tracking-[0.12em] uppercase transition-colors"
              style={{
                color: autoScan ? "#57e0a0" : "#7c879e",
                borderColor: autoScan ? "rgba(87,224,160,0.45)" : "rgba(43,52,70,0.8)",
              }}
            >
              auto
            </button>
            <button
              type="button"
              onClick={onScan}
              disabled={scanning}
              className="rounded-sm border border-gold/40 bg-gold/10 px-1.5 py-[2px] font-mono text-[8.5px] tracking-[0.12em] text-gold uppercase transition-colors hover:bg-gold/20 disabled:opacity-50"
            >
              {scanning ? "…" : "scan"}
            </button>
          </div>
        }
      />
      <div className="flex flex-wrap gap-1 border-b border-line/60 px-3 py-1.5">
        {(["all", ...MARKETS.map((market) => market.key)] as const).map((key) => (
          <Chip
            key={key}
            active={filter === key}
            color={key === "all" ? "#a79bff" : FOCUS_COLOR[key]}
            onClick={() => setFilter(key)}
          >
            {key === "all" ? "all" : MARKETS.find((market) => market.key === key)?.short}
          </Chip>
        ))}
        <span className="ml-auto self-center font-mono text-[8px] tracking-[0.12em] text-muted/70 uppercase">
          utc timestamps
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {visible.length === 0 ? (
          <div className="p-6 text-center font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
            no signals on this desk yet — run a swarm scan
          </div>
        ) : null}
        {visible.map((signal) => {
          const accent = FOCUS_COLOR[signal.market] ?? "#f2c46b";
          return (
            <article
              key={signal.id}
              className="animate-rise border-b border-line/40 px-3 py-2.5 transition-colors hover:bg-white/[0.025]"
            >
              <div className="flex items-center gap-1.5">
                <DirectionPill direction={signal.direction} />
                <span className="font-mono text-[11px] font-medium text-ink">{signal.symbol}</span>
                <span className="rounded-[2px] border border-line/70 px-1 font-mono text-[8px] tracking-[0.1em] text-muted">
                  {signal.timeframe}
                </span>
                <span className="ml-auto font-mono text-[8.5px] tabular-nums text-muted/80">
                  {formatUtcClock(signal.createdAt)}
                </span>
              </div>

              <div className="mt-1.5 flex items-center gap-1.5">
                <span
                  className="font-mono text-[9.5px] tracking-[0.08em]"
                  style={{ color: accent }}
                  role="button"
                  tabIndex={0}
                  onClick={() => onOpenAgent(signal.agentId)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") onOpenAgent(signal.agentId);
                  }}
                >
                  {signal.codename}
                </span>
                <span className="truncate font-mono text-[8.5px] text-muted/80">{signal.role}</span>
                <span className="ml-auto shrink-0 font-mono text-[8.5px] text-muted">
                  acc <span className="text-ink/80">{signal.accuracy.toFixed(1)}%</span>
                </span>
              </div>

              <p className="mt-1.5 line-clamp-2 text-[10.5px] leading-relaxed text-ink/60">{signal.rationale}</p>

              <div className="mt-1.5 flex items-center gap-2">
                <div className="flex-1">
                  <Meter value={signal.confidence} color={accent} />
                </div>
                <span className="font-mono text-[8.5px] tabular-nums text-muted">{signal.confidence}%</span>
                <span className="font-mono text-[8.5px] tabular-nums text-muted/80">
                  {formatPrice(signal.entry, 2)} → <span className="text-ink/70">{formatPrice(signal.target, 2)}</span>
                </span>
                <button
                  type="button"
                  onClick={() => onOpenAgent(signal.agentId)}
                  className="rounded-[2px] border border-line/70 px-1 py-[1px] font-mono text-[8px] tracking-[0.1em] text-muted uppercase transition-colors hover:border-gold/40 hover:text-gold"
                >
                  agent
                </button>
              </div>
            </article>
          );
        })}
      </div>

      <div className="flex items-center justify-between border-t border-line/70 bg-black/20 px-3 py-1.5">
        <span className="label">stopped {formatPrice(visible[0]?.stop ?? 0, 2)} · confidence weighted</span>
        <span className="font-mono text-[8.5px] tracking-[0.12em] text-mint uppercase">
          {visible.filter((signal) => signal.direction === "bullish").length}L /{" "}
          {visible.filter((signal) => signal.direction === "bearish").length}S
        </span>
      </div>
    </div>
  );
}
