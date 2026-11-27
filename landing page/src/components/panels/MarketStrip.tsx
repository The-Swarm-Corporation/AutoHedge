"use client";

import { FOCUS_COLOR, formatSignedPct } from "@/lib/ui";
import { MARKETS, formatPrice, type MarketKey } from "@/lib/market";
import type { ConsensusView, InstrumentView, MarketSnapshot } from "@/lib/types";

export function TickerTape({ instruments }: { instruments: InstrumentView[] }) {
  const items = [...instruments, ...instruments];
  return (
    <div className="ticker-mask relative overflow-hidden border-y border-line/70 bg-carbon/80">
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-void to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-void to-transparent" />
      <div className="ticker-track items-center gap-6 py-1.5">
        {items.map((instrument, index) => (
          <div key={`${instrument.id}-${index}`} className="flex shrink-0 items-center gap-2 whitespace-nowrap">
            <span className="font-mono text-[10px] tracking-[0.1em] text-gold/90">{instrument.symbol}</span>
            <span className="font-mono text-[10px] tabular-nums text-ink/80">
              {formatPrice(instrument.price, instrument.decimals)}
            </span>
            <span
              className="font-mono text-[10px] tabular-nums"
              style={{ color: instrument.changePct >= 0 ? "#57e0a0" : "#ff7d88" }}
            >
              {formatSignedPct(instrument.changePct)}
            </span>
            <span className="text-[8px] text-line-bright">◆</span>
          </div>
        ))}
      </div>
    </div>
  );
}

type MarketStripProps = {
  sessions: MarketSnapshot["sessions"];
  instruments: InstrumentView[];
  consensus: ConsensusView[];
  agentCounts: Record<string, number>;
  selectedMarket: MarketKey;
  onMarketChange: (market: MarketKey) => void;
};

export function MarketStrip({
  sessions,
  instruments,
  consensus,
  agentCounts,
  selectedMarket,
  onMarketChange,
}: MarketStripProps) {
  return (
    <div className="grid grid-cols-2 gap-2 xl:grid-cols-4">
      {MARKETS.map((market) => {
        const accent = FOCUS_COLOR[market.key];
        const session = sessions.find((item) => item.market === market.key);
        const own = instruments.filter((item) => item.market === market.key);
        const avgPct = own.length > 0 ? own.reduce((sum, item) => sum + item.changePct, 0) / own.length : 0;
        const view = consensus.find((item) => item.market === market.key);
        const selected = selectedMarket === market.key;
        const positive = avgPct >= 0;

        return (
          <button
            key={market.key}
            type="button"
            onClick={() => onMarketChange(market.key)}
            className="panel group relative overflow-hidden rounded-lg px-3 py-2 text-left transition-all hover:border-line-bright"
            style={{ borderColor: selected ? `${accent}66` : undefined, boxShadow: selected ? `0 0 24px -12px ${accent}` : undefined }}
          >
            <span className="absolute inset-x-0 top-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${accent}aa, transparent)` }} />
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-[9.5px] font-semibold tracking-[0.16em]" style={{ color: accent }}>
                  {market.short}
                </span>
                <span className="truncate font-mono text-[8px] tracking-[0.1em] text-muted/80 uppercase">{market.label}</span>
              </div>
              <span
                className="flex items-center gap-1 rounded-sm px-1 py-[1px] font-mono text-[8px] tracking-[0.12em] uppercase"
                style={{
                  color: session?.status === "open" ? "#57e0a0" : "#ff9b9b",
                  background: session?.status === "open" ? "rgba(87,224,160,0.1)" : "rgba(255,125,136,0.08)",
                }}
              >
                <span
                  className="h-1 w-1 rounded-full"
                  style={{ background: session?.status === "open" ? "#57e0a0" : "#ff7d88" }}
                />
                {session?.label ?? "—"}
              </span>
            </div>
            <div className="mt-1.5 flex items-end justify-between gap-2">
              <div>
                <div className="font-mono text-[15px] font-semibold tabular-nums" style={{ color: positive ? "#8ef5c4" : "#ff9ba3" }}>
                  {formatSignedPct(avgPct)}
                </div>
                <div className="font-mono text-[8px] tracking-[0.1em] text-muted/80 uppercase">
                  {agentCounts[market.key] ?? 0} agents · {view?.count ?? 0} signals
                </div>
              </div>
              <div className="text-right">
                <div className="font-mono text-[8px] tracking-[0.12em] text-muted/80 uppercase">consensus</div>
                <div
                  className="font-mono text-[10px] tracking-[0.1em] uppercase"
                  style={{ color: view?.bias === "long" ? "#57e0a0" : view?.bias === "short" ? "#ff7d88" : "#f2c46b" }}
                >
                  {view ? `${view.bias} ${view.score > 0 ? "+" : ""}${view.score}` : "—"}
                </div>
              </div>
            </div>
            <div className="mt-1.5 h-[2px] w-full overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${Math.min(100, Math.max(6, Math.abs(avgPct) * 90 + 18))}%`,
                  background: `linear-gradient(90deg, ${accent}44, ${accent})`,
                }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}
