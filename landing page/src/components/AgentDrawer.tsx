"use client";

import { useEffect, useState } from "react";
import { DirectionPill, FocusBadge, Meter, StatusPill } from "@/components/ui";
import { FOCUS_COLOR, focusLabel, formatMoney, formatUtcClock } from "@/lib/ui";
import type { AgentView, SignalView } from "@/lib/types";

type AgentDetail = {
  agent: AgentView;
  signals: SignalView[];
  events: { id: number; kind: string; message: string; createdAt: string }[];
};

export function AgentDrawer({ agentId, onClose }: { agentId: number | null; onClose: () => void }) {
  const [detail, setDetail] = useState<AgentDetail | null>(null);

  useEffect(() => {
    if (agentId === null) return;
    const controller = new AbortController();
    fetch(`/api/agents/${agentId}`, { signal: controller.signal })
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error("not found"))))
      .then((payload: AgentDetail) => setDetail(payload))
      .catch((error) => {
        if ((error as Error).name !== "AbortError") console.error(error);
      });
    return () => controller.abort();
  }, [agentId]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (agentId === null) return null;
  const current = detail && detail.agent.id === agentId ? detail : null;
  const agent = current?.agent;
  const accent = agent ? FOCUS_COLOR[agent.focus] ?? "#f2c46b" : "#f2c46b";

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Close agent inspector"
        onClick={onClose}
        className="absolute inset-0 bg-black/65 backdrop-blur-sm"
      />
      <aside className="relative flex h-full w-full max-w-[430px] flex-col overflow-hidden border-l border-line bg-panel shadow-[0_0_80px_rgba(0,0,0,0.9)]">
        <div
          className="pointer-events-none absolute inset-x-0 top-0 h-40 opacity-50"
          style={{ background: `radial-gradient(ellipse at 50% -20%, ${accent}55, transparent 70%)` }}
        />
        <div className="relative flex items-start justify-between gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0">
            <div className="label">agent inspector</div>
            <h2 className="mt-0.5 truncate font-mono text-lg font-semibold tracking-tight text-ink">
              {agent?.codename ?? "loading…"}
            </h2>
            <p className="truncate font-mono text-[10px] text-muted">
              {agent ? `${agent.callsign} · ${agent.role}` : "resolving neural profile"}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-sm border border-line px-2 py-1 font-mono text-[10px] text-muted transition-colors hover:border-gold/50 hover:text-gold"
          >
            esc ✕
          </button>
        </div>

        <div className="relative flex-1 overflow-y-auto px-4 py-3">
          {agent ? (
            <>
              <div className="flex flex-wrap items-center gap-1.5">
                <FocusBadge focus={agent.focus} />
                <StatusPill status={agent.status} />
                <span className="rounded-sm border border-line/80 px-1.5 py-[2px] font-mono text-[8.5px] tracking-[0.1em] text-muted">
                  {agent.model} · gen-{agent.generation}
                </span>
              </div>

              <div className="mt-3 grid grid-cols-2 gap-2">
                <Stat label="Accuracy" value={`${agent.accuracy.toFixed(1)}%`} accent={accent} />
                <Stat label="Net P&L" value={`${formatMoney(agent.pnl, 0)}`} accent={agent.pnl >= 0 ? "#57e0a0" : "#ff7d88"} />
                <Stat label="Signals" value={agent.signalsCount.toLocaleString()} accent="#5be9e0" />
                <Stat label="Inference" value={`${agent.latencyMs}ms`} accent="#a79bff" />
              </div>

              <div className="mt-3 rounded-md border border-line/70 bg-black/25 p-2.5">
                <div className="flex items-center justify-between">
                  <span className="label">weighted confidence</span>
                  <span className="font-mono text-[10px]" style={{ color: accent }}>
                    {focusLabel(agent.focus)} desk
                  </span>
                </div>
                <div className="mt-1.5">
                  <Meter value={agent.accuracy} color={accent} height={4} />
                </div>
                <div className="mt-2 font-mono text-[9px] leading-relaxed text-muted">
                  mission · <span className="text-ink/75">{agent.specialty}</span>
                </div>
              </div>

              <div className="mt-4">
                <div className="label mb-1.5">recent signals</div>
                {(current?.signals.length ?? 0) === 0 ? (
                  <p className="rounded-sm border border-line/60 bg-white/[0.02] px-2 py-2 font-mono text-[9.5px] text-muted">
                    no published signals in the active window
                  </p>
                ) : (
                  <div className="space-y-1.5">
                    {(current?.signals ?? []).map((signal) => (
                      <div key={signal.id} className="rounded-sm border border-line/60 bg-white/[0.02] px-2 py-1.5">
                        <div className="flex items-center gap-1.5">
                          <DirectionPill direction={signal.direction} />
                          <span className="font-mono text-[10px] text-ink/90">{signal.symbol}</span>
                          <span className="ml-auto font-mono text-[8.5px] text-muted">{formatUtcClock(signal.createdAt)}</span>
                        </div>
                        <div className="mt-1 flex items-center gap-2 font-mono text-[8.5px] text-muted">
                          <span>conf {signal.confidence}%</span>
                          <span>tf {signal.timeframe}</span>
                          <span className="text-mint/80">tgt {signal.target.toFixed(2)}</span>
                          <span className="text-rose/80">stop {signal.stop.toFixed(2)}</span>
                        </div>
                        <p className="mt-1 line-clamp-2 text-[9.5px] leading-relaxed text-muted/90">{signal.rationale}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-4">
                <div className="label mb-1.5">agent activity</div>
                <div className="space-y-1">
                  {(current?.events.length ?? 0) === 0 ? (
                    <p className="font-mono text-[9.5px] text-muted">no telemetry captured yet</p>
                  ) : null}
                  {(current?.events ?? []).map((event) => (
                    <div key={event.id} className="flex items-start gap-2 font-mono text-[9px] leading-relaxed">
                      <span className="mt-[3px] h-1 w-1 shrink-0 rounded-full" style={{ background: accent }} />
                      <span className="text-muted/70">{formatUtcClock(event.createdAt)}</span>
                      <span className="text-ink/65">{event.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, index) => (
                <div key={index} className="h-8 animate-pulse rounded-sm bg-white/[0.03]" />
              ))}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div className="rounded-sm border border-line/70 bg-black/25 px-2 py-1.5">
      <div className="label">{label}</div>
      <div className="mt-0.5 font-mono text-[15px] font-semibold tabular-nums" style={{ color: accent }}>
        {value}
      </div>
    </div>
  );
}
