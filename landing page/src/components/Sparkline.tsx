"use client";

import { useId } from "react";

type SparklineProps = {
  data: number[];
  color: string;
  width?: number;
  height?: number;
  strokeWidth?: number;
  showFill?: boolean;
  className?: string;
};

export function Sparkline({
  data,
  color,
  width = 120,
  height = 34,
  strokeWidth = 1.4,
  showFill = true,
  className,
}: SparklineProps) {
  const gradientId = useId().replace(/[:]/g, "");
  const points = data.length > 1 ? data : [data[0] ?? 0, data[0] ?? 0];
  const min = Math.min(...points);
  const max = Math.max(...points);
  const spread = max - min || Math.max(0.0001, max * 0.0002);

  const coords = points.map((value, index) => {
    const x = (index / (points.length - 1)) * width;
    const y = height - ((value - min) / spread) * (height - 4) - 2;
    return [x, y] as const;
  });

  const line = coords
    .map(([x, y], index) => `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`)
    .join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;
  const last = coords[coords.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={`spark-${gradientId}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {showFill ? <path d={area} fill={`url(#spark-${gradientId})`} /> : null}
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {last ? <circle cx={last[0]} cy={last[1]} r={1.9} fill={color} /> : null}
    </svg>
  );
}
