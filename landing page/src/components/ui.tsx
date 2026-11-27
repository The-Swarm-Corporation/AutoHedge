"use client";

import type { ReactNode } from "react";
import { FOCUS_COLOR, STATUS_COLOR, focusLabel } from "@/lib/ui";
import type { AgentStatus } from "@/lib/types";
import type { MarketKey } from "@/lib/market";

export function Delta({ value, decimals = 2, className = "" }: { value: number; decimals?: number; className?: string }) {
  const positive = value >= 0;
  return (
    <span
      className={`font-mono tabular-nums ${positive ? "text-mint" : "text-rose"} ${className}`}
    >
      {positive ? "▲" : "▼"} {Math.abs(value).toFixed(decimals)}%
    </span>
  );
}

export function FocusBadge({ focus, compact = false }: { focus: MarketKey | "macro"; compact?: boolean }) {
  const color = FOCUS_COLOR[focus] ?? "#7c879e";
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-sm border px-1.5 py-[2px] font-mono text-[9px] tracking-[0.14em]"
      style={{ borderColor: `${color}44`, color, background: `${color}0f` }}
    >
      <span className="h-1 w-1 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
      {compact ? focusLabel(focus) : focusLabel(focus)}
    </span>
  );
}

export function StatusPill({ status }: { status: AgentStatus }) {
  const color = STATUS_COLOR[status] ?? "#7c879e";
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-[9.5px] tracking-[0.14em] uppercase" style={{ color }}>
      <span
        className={`h-1.5 w-1.5 rounded-full ${status === "active" || status === "scanning" ? "animate-pulse-soft" : ""}`}
        style={{ background: color, boxShadow: `0 0 7px ${color}` }}
      />
      {status}
    </span>
  );
}

export function DirectionPill({ direction }: { direction: "bullish" | "bearish" | "neutral" }) {
  const map = {
    bullish: { color: "#57e0a0", label: "LONG" },
    bearish: { color: "#ff7d88", label: "SHORT" },
    neutral: { color: "#f2c46b", label: "FLAT" },
  } as const;
  const style = map[direction];
  return (
    <span
      className="rounded-sm border px-1.5 py-[2px] font-mono text-[9.5px] font-semibold tracking-[0.14em]"
      style={{ color: style.color, borderColor: `${style.color}55`, background: `${style.color}12` }}
    >
      {style.label}
    </span>
  );
}

export function Meter({ value, color, height = 3 }: { value: number; color: string; height?: number }) {
  return (
    <div className="w-full overflow-hidden rounded-full bg-white/[0.06]" style={{ height }}>
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{
          width: `${Math.max(2, Math.min(100, value))}%`,
          background: `linear-gradient(90deg, ${color}66, ${color})`,
          boxShadow: `0 0 8px ${color}66`,
        }}
      />
    </div>
  );
}

export function PanelHeader({
  title,
  subtitle,
  right,
  accent = "#f2c46b",
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
  accent?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line/70 px-3.5 py-2.5">
      <div className="flex min-w-0 items-center gap-2">
        <span className="h-3 w-[2px] rounded-full" style={{ background: accent, boxShadow: `0 0 8px ${accent}` }} />
        <h2 className="truncate font-mono text-[10.5px] font-semibold tracking-[0.18em] text-ink/90 uppercase">{title}</h2>
        {subtitle ? <span className="truncate font-mono text-[9px] tracking-[0.12em] text-muted uppercase">{subtitle}</span> : null}
      </div>
      {right}
    </div>
  );
}

export function Chip({
  active,
  children,
  onClick,
  color = "#f2c46b",
}: {
  active?: boolean;
  children: ReactNode;
  onClick?: () => void;
  color?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-sm border px-2 py-[3px] font-mono text-[9.5px] tracking-[0.13em] uppercase transition-colors"
      style={{
        borderColor: active ? `${color}88` : "rgba(43,52,70,0.8)",
        color: active ? color : "#7c879e",
        background: active ? `${color}14` : "transparent",
      }}
    >
      {children}
    </button>
  );
}
