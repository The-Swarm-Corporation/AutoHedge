"use client";

import { useState } from "react";
import { Sparkline } from "@/components/Sparkline";
import { Chip, Delta, PanelHeader } from "@/components/ui";
import { FOCUS_COLOR } from "@/lib/ui";
import { MARKETS, formatCompact, formatPrice, type MarketKey } from "@/lib/market";
import type { InstrumentView, MarketSnapshot } from "@/lib/types";

type WatchlistProps = {
  instruments: InstrumentView[];
  sessions: MarketSnapshot["sessions"];
  selectedSymbol: string;
  selectedMarket: MarketKey;
  onSelect: (instrument: InstrumentView) => void;
  onMarketChange: (market: MarketKey) => void;
};

export function Watchlist({
  instruments,
  sessions,
  selectedSymbol,
  selectedMarket,
  onSelect,
  onMarketChange,
}: WatchlistProps) {
  const [filter, setFilter] = useState<"all" | MarketKey>("all");
  const visible = filter === "all" ? instruments : instruments.filter((item) => item.market === filter);

  return (
    <div className="panel flex h-full flex-col overflow-hidden rounded-xl">
      <PanelHeader
        title="Global Watchlist"
        subtitle={`${instruments.length} instruments`}
        right={
          <button
            type="button"
            className="font-mono text-[9px] tracking-[0.14em] text-muted uppercase transition-colors hover:text-gold"
            onClick={() => setFilter("all")}
          >
            sync ↻
          </button>
        }
      />
      <div className="flex flex-wrap gap-1 border-b border-line/60 px-3 py-2">
        {(["all", ...MARKETS.map((market) => market.key)] as const).map((key) => (
          <Chip
            key={key}
            active={filter === key}
            color={key === "all" ? "#f2c46b" : FOCUS_COLOR[key]}
            onClick={() => {
              setFilter(key);
              if (key !== "all") onMarketChange(key);
            }}
          >
            {key === "all" ? "all" : MARKETS.find((market) => market.key === key)?.short}
          </Chip>
        ))}
      </div>

      <div className="flex-1 divide-y divide-line/50 overflow-y-auto">
        {visible.map((instrument) => {
          const selected = instrument.symbol === selectedSymbol;
          const accent = FOCUS_COLOR[instrument.market] ?? "#f2c46b";
          const session = sessions.find((item) => item.market === instrument.market);
          return (
            <button
              key={instrument.id}
              type="button"
              onClick={() => onSelect(instrument)}
              className="group relative flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-white/[0.035]"
              style={{ background: selected ? `${accent}0c` : undefined }}
            >
              <span
                className="absolute inset-y-0 left-0 w-[2px] transition-opacity"
                style={{ background: accent, opacity: selected ? 1 : 0.18 }}
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="truncate font-mono text-[11px] font-medium tracking-wide text-ink">{instrument.symbol}</span>
                  <span className="rounded-[2px] border border-line/80 px-1 font-mono text-[8px] tracking-[0.1em] text-muted uppercase">
                    {instrument.kind}
                  </span>
                </div>
                <div className="mt-0.5 flex items-center gap-1.5">
                  <span className="truncate font-mono text-[9px] tracking-[0.04em] text-muted">{instrument.name}</span>
                  <span
                    className="h-1 w-1 shrink-0 rounded-full"
                    style={{
                      background: session?.status === "open" ? "#57e0a0" : "#7c879e",
                      boxShadow: session?.status === "open" ? "0 0 6px #57e0a0" : "none",
                    }}
                  />
                </div>
              </div>
              <div className="hidden shrink-0 sm:block lg:hidden xl:block">
                <Sparkline
                  data={instrument.sparkline}
                  color={(instrument.changePct ?? 0) >= 0 ? "#57e0a0" : "#ff7d88"}
                  width={62}
                  height={26}
                />
              </div>
              <div className="shrink-0 text-right">
                <div className="font-mono text-[11.5px] tabular-nums text-ink">
                  {formatPrice(instrument.price, instrument.decimals)}
                </div>
                <div className="mt-0.5 flex items-center justify-end gap-1.5">
                  <Delta value={instrument.changePct} className="text-[9.5px]" />
                  <span className="hidden font-mono text-[8.5px] text-muted/80 2xl:inline">{formatCompact(instrument.volume)}</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-2 gap-px border-t border-line/70 bg-line/50">
        {MARKETS.map((market) => {
          const session = sessions.find((item) => item.market === market.key);
          const isSelected = selectedMarket === market.key;
          return (
            <button
              key={market.key}
              type="button"
              onClick={() => onMarketChange(market.key)}
              className="bg-panel px-2.5 py-1.5 text-left transition-colors hover:bg-panel-2"
            >
              <div className="flex items-center gap-1.5">
                <span
                  className="h-1 w-1 rounded-full"
                  style={{
                    background: session?.status === "open" ? "#57e0a0" : "#7c879e",
                    boxShadow: session?.status === "open" ? "0 0 6px #57e0a0" : "none",
                  }}
                />
                <span
                  className="font-mono text-[8.5px] tracking-[0.14em] uppercase"
                  style={{ color: isSelected ? FOCUS_COLOR[market.key] : "#7c879e" }}
                >
                  {market.short}
                </span>
                <span className="ml-auto font-mono text-[8px] tracking-[0.1em] text-muted/80 uppercase">
                  {session?.label.replace("-MARKET", "")}
                </span>
              </div>
              <div className="mt-0.5 truncate font-mono text-[8px] text-muted/70">{market.timezoneLabel}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
