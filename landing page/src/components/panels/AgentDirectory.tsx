"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FocusBadge, Meter, PanelHeader, StatusPill } from "@/components/ui";
import { FOCUS_COLOR, formatMoney } from "@/lib/ui";
import type { AgentView } from "@/lib/types";

type AgentListResponse = {
  items: AgentView[];
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
};

const FOCUS_FILTERS = [
  { key: "all", label: "all" },
  { key: "gold", label: "gold" },
  { key: "forex", label: "fx" },
  { key: "us", label: "usa" },
  { key: "india", label: "india" },
  { key: "macro", label: "macro" },
];

export function AgentDirectory({
  onOpenAgent,
  agentTotal,
}: {
  onOpenAgent: (id: number) => void;
  agentTotal: number;
}) {
  const [query, setQuery] = useState("");
  const [focus, setFocus] = useState("all");
  const [status, setStatus] = useState("all");
  const [sort, setSort] = useState("accuracy");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<AgentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: query,
        focus,
        status,
        sort,
        page: String(page),
        perPage: "12",
      });
      const response = await fetch(`/api/agents?${params.toString()}`, { signal: controller.signal });
      if (!response.ok) throw new Error("agent fetch failed");
      const payload = (await response.json()) as AgentListResponse;
      setData(payload);
    } catch (error) {
      if ((error as Error).name !== "AbortError") console.error(error);
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, [focus, page, query, sort, status]);

  useEffect(() => {
    const timer = setTimeout(load, query ? 260 : 0);
    return () => clearTimeout(timer);
  }, [load, query]);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const items = data?.items ?? [];
  const totalPages = data?.totalPages ?? 1;
  const total = data?.total ?? agentTotal;

  return (
    <div className="panel flex h-[540px] flex-col overflow-hidden rounded-xl">
      <PanelHeader
        title="Agent Grid"
        subtitle={`${total.toLocaleString()} / ${agentTotal.toLocaleString()} agents`}
        accent="#57e0a0"
        right={
          <span className="flex items-center gap-1.5 font-mono text-[8.5px] tracking-[0.12em] uppercase">
            <span className={`h-1.5 w-1.5 rounded-full ${loading ? "bg-gold" : "bg-mint"} ${loading ? "animate-pulse" : ""}`} />
            <span className={loading ? "text-gold" : "text-mint"}>{loading ? "syncing" : "live"}</span>
          </span>
        }
      />

      <div className="flex flex-wrap items-center gap-1.5 border-b border-line/60 px-3 py-2">
        <div className="relative min-w-[160px] flex-1">
          <span className="pointer-events-none absolute top-1/2 left-2 -translate-y-1/2 font-mono text-[10px] text-muted/70">⌕</span>
          <input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder="search 550 agents · role · model"
            className="w-full rounded-sm border border-line/80 bg-black/30 py-1 pr-2 pl-6 font-mono text-[10px] tracking-wide text-ink placeholder:text-muted/60 focus:border-gold/50 focus:outline-none"
          />
        </div>
        <select
          value={sort}
          onChange={(event) => {
            setSort(event.target.value);
            setPage(1);
          }}
          className="rounded-sm border border-line/80 bg-black/30 px-1.5 py-1 font-mono text-[9px] tracking-[0.08em] text-muted uppercase focus:border-gold/50 focus:outline-none"
        >
          <option value="accuracy">sort · accuracy</option>
          <option value="pnl">sort · p&amp;l</option>
          <option value="signals">sort · signals</option>
          <option value="latency">sort · latency</option>
        </select>
        <select
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
          className="rounded-sm border border-line/80 bg-black/30 px-1.5 py-1 font-mono text-[9px] tracking-[0.08em] text-muted uppercase focus:border-gold/50 focus:outline-none"
        >
          <option value="all">status · all</option>
          <option value="active">active</option>
          <option value="scanning">scanning</option>
          <option value="debating">debating</option>
          <option value="idle">idle</option>
          <option value="risk-hold">risk-hold</option>
        </select>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-line/60 px-3 py-1.5">
        {FOCUS_FILTERS.map((filter) => {
          const active = focus === filter.key;
          const color = filter.key === "all" ? "#f2c46b" : FOCUS_COLOR[filter.key] ?? "#7c879e";
          return (
            <button
              key={filter.key}
              type="button"
              onClick={() => {
                setFocus(filter.key);
                setPage(1);
              }}
              className="rounded-sm border px-1.5 py-[2px] font-mono text-[8.5px] tracking-[0.12em] uppercase transition-colors"
              style={{
                color: active ? color : "#7c879e",
                borderColor: active ? `${color}88` : "rgba(43,52,70,0.7)",
                background: active ? `${color}12` : "transparent",
              }}
            >
              {filter.label}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-left">
          <thead className="sticky top-0 z-10 bg-panel-2/95 backdrop-blur">
            <tr className="font-mono text-[8px] tracking-[0.14em] text-muted uppercase">
              <th className="px-3 py-1.5 font-medium">Agent</th>
              <th className="hidden px-2 py-1.5 font-medium md:table-cell">Mandate</th>
              <th className="px-2 py-1.5 font-medium">Desk</th>
              <th className="hidden px-2 py-1.5 font-medium lg:table-cell">Model</th>
              <th className="px-2 py-1.5 font-medium">Status</th>
              <th className="px-2 py-1.5 font-medium">Accuracy</th>
              <th className="hidden px-2 py-1.5 text-right font-medium sm:table-cell">P&amp;L</th>
              <th className="px-3 py-1.5 text-right font-medium">ms</th>
            </tr>
          </thead>
          <tbody>
            {items.map((agent) => {
              const accent = FOCUS_COLOR[agent.focus] ?? "#7c879e";
              return (
                <tr
                  key={agent.id}
                  onClick={() => onOpenAgent(agent.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") onOpenAgent(agent.id);
                  }}
                  tabIndex={0}
                  className="group cursor-pointer border-t border-line/40 transition-colors hover:bg-white/[0.035] focus:bg-white/[0.05] focus:outline-none"
                >
                  <td className="px-3 py-1.5">
                    <div className="flex items-center gap-1.5">
                      <span
                        className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-[3px] border font-mono text-[7.5px]"
                        style={{ borderColor: `${accent}55`, color: accent, background: `${accent}12` }}
                      >
                        {agent.codename.slice(0, 2)}
                      </span>
                      <div className="min-w-0">
                        <div className="truncate font-mono text-[10px] text-ink/90 group-hover:text-gold">{agent.codename}</div>
                        <div className="truncate font-mono text-[8px] text-muted/70">{agent.callsign}</div>
                      </div>
                    </div>
                  </td>
                  <td className="hidden max-w-[170px] px-2 py-1.5 md:table-cell">
                    <div className="truncate font-mono text-[9px] text-ink/70">{agent.role}</div>
                    <div className="truncate font-mono text-[8px] text-muted/70">{agent.specialty}</div>
                  </td>
                  <td className="px-2 py-1.5">
                    <FocusBadge focus={agent.focus} />
                  </td>
                  <td className="hidden px-2 py-1.5 lg:table-cell">
                    <span className="font-mono text-[8.5px] text-muted">{agent.model}</span>
                    <div className="font-mono text-[7.5px] text-muted/60">gen-{agent.generation}</div>
                  </td>
                  <td className="px-2 py-1.5">
                    <StatusPill status={agent.status} />
                  </td>
                  <td className="px-2 py-1.5">
                    <div className="flex items-center gap-1.5">
                      <div className="w-12">
                        <Meter value={agent.accuracy} color={accent} height={2.5} />
                      </div>
                      <span className="font-mono text-[9px] tabular-nums text-ink/75">{agent.accuracy.toFixed(1)}</span>
                    </div>
                  </td>
                  <td className="hidden px-2 py-1.5 text-right sm:table-cell">
                    <span
                      className="font-mono text-[9px] tabular-nums"
                      style={{ color: agent.pnl >= 0 ? "#57e0a0" : "#ff7d88" }}
                    >
                      {formatMoney(agent.pnl, 0)}
                    </span>
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono text-[9px] tabular-nums text-muted">{agent.latencyMs}</td>
                </tr>
              );
            })}
            {!loading && items.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
                  no agents match this filter
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
        {loading && items.length === 0 ? (
          <div className="space-y-1 p-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-7 animate-pulse rounded-sm bg-white/[0.03]" />
            ))}
          </div>
        ) : null}
      </div>

      <div className="flex items-center justify-between gap-2 border-t border-line/70 bg-black/20 px-3 py-1.5">
        <span className="font-mono text-[8.5px] tracking-[0.1em] text-muted uppercase">
          page {data?.page ?? page} / {totalPages}
        </span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((value) => Math.max(1, value - 1))}
            className="rounded-sm border border-line/80 px-2 py-[2px] font-mono text-[9px] tracking-[0.1em] text-muted uppercase transition-colors hover:text-gold disabled:opacity-30"
          >
            prev
          </button>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
            className="rounded-sm border border-line/80 px-2 py-[2px] font-mono text-[9px] tracking-[0.1em] text-muted uppercase transition-colors hover:text-gold disabled:opacity-30"
          >
            next
          </button>
          <span className="ml-1 font-mono text-[8.5px] text-muted/70">12 / page · 550 total</span>
        </div>
      </div>
    </div>
  );
}
