"use client";

import React, { useId, useState } from "react";

// =============================================================================
// LINE / AREA CHART
// =============================================================================

export interface ChartDataPoint {
  label: string;
  value: number;
}

interface LineChartProps {
  data: ChartDataPoint[];
  height?: number;
  color?: string;
  formatValue?: (val: number) => string;
  emptyMessage?: string;
}

export function LineChart({
  data,
  height = 240,
  color = "#10b981",
  formatValue = (v) => v.toLocaleString(),
  emptyMessage = "No data available for this period",
}: LineChartProps) {
  const gradientId = useId();
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="chart-empty" style={{ height }}>
        <span>{emptyMessage}</span>
      </div>
    );
  }

  const values = data.map((d) => d.value);
  const minVal = 0;
  const maxVal = Math.max(...values, 1);

  const paddingX = 40;
  const paddingY = 30;
  const width = 600; // SVG coordinate system
  const plotWidth = width - paddingX * 2;
  const plotHeight = height - paddingY * 2;

  const points = data.map((d, i) => {
    const x = paddingX + (i / Math.max(data.length - 1, 1)) * plotWidth;
    const y = paddingY + plotHeight - ((d.value - minVal) / (maxVal - minVal)) * plotHeight;
    return { x, y, ...d };
  });

  const pathD = points.reduce((acc, p, i) => {
    return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, "");

  const areaD =
    points.length > 0
      ? `${pathD} L ${points[points.length - 1].x} ${height - paddingY} L ${points[0].x} ${
          height - paddingY
        } Z`
      : "";

  const gridSteps = 4;
  const yLabels = Array.from({ length: gridSteps + 1 }, (_, i) => {
    const val = minVal + ((maxVal - minVal) / gridSteps) * (gridSteps - i);
    const y = paddingY + (plotHeight / gridSteps) * i;
    return { val, y };
  });

  const activePoint = hoveredIdx !== null ? points[hoveredIdx] : null;

  return (
    <div className="chart-wrapper" style={{ height }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="chart-svg"
        preserveAspectRatio="none"
        onMouseLeave={() => setHoveredIdx(null)}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.32" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal Grid lines */}
        {yLabels.map((g, i) => (
          <g key={i}>
            <line
              x1={paddingX}
              y1={g.y}
              x2={width - paddingX}
              y2={g.y}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeDasharray="4 4"
            />
            <text
              x={paddingX - 8}
              y={g.y + 4}
              textAnchor="end"
              fill="rgba(255, 255, 255, 0.4)"
              fontSize="10"
              fontFamily="monospace"
            >
              {formatValue(g.val)}
            </text>
          </g>
        ))}

        {/* Gradient fill */}
        {areaD && <path d={areaD} fill={`url(#${gradientId})`} />}

        {/* Line */}
        {pathD && (
          <path
            d={pathD}
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* Hover hit targets & dots */}
        {points.map((p, i) => (
          <g key={i} onMouseEnter={() => setHoveredIdx(i)}>
            <circle
              cx={p.x}
              cy={p.y}
              r={hoveredIdx === i ? 5 : 3}
              fill={hoveredIdx === i ? "#fff" : color}
              stroke={color}
              strokeWidth={hoveredIdx === i ? 2 : 1}
            />
            <rect
              x={p.x - plotWidth / data.length / 2}
              y={0}
              width={plotWidth / data.length}
              height={height}
              fill="transparent"
              style={{ cursor: "pointer" }}
            />
          </g>
        ))}

        {/* Vertical hover marker */}
        {activePoint && (
          <line
            x1={activePoint.x}
            y1={paddingY}
            x2={activePoint.x}
            y2={height - paddingY}
            stroke="rgba(255, 255, 255, 0.25)"
            strokeDasharray="2 2"
          />
        )}
      </svg>

      {/* Interactive HTML Tooltip */}
      {activePoint && (
        <div
          className="chart-tooltip"
          style={{
            left: `${(activePoint.x / width) * 100}%`,
            top: `${(activePoint.y / height) * 100}%`,
          }}
        >
          <div className="tooltip-date">{activePoint.label}</div>
          <div className="tooltip-val" style={{ color }}>
            {formatValue(activePoint.value)}
          </div>
        </div>
      )}

      {/* Bottom X-axis labels */}
      <div className="chart-x-labels">
        {data.length > 0 && <span>{data[0].label}</span>}
        {data.length > 2 && (
          <span>{data[Math.floor(data.length / 2)].label}</span>
        )}
        {data.length > 1 && <span>{data[data.length - 1].label}</span>}
      </div>
    </div>
  );
}

// =============================================================================
// BAR CHART
// =============================================================================

export interface BarChartItem {
  label: string;
  value: number;
}

interface BarChartProps {
  data: BarChartItem[];
  height?: number;
  color?: string;
  formatValue?: (val: number) => string;
  emptyMessage?: string;
}

export function BarChart({
  data,
  height = 240,
  color = "#38bdf8",
  formatValue = (v) => v.toLocaleString(),
  emptyMessage = "No data available for this period",
}: BarChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="chart-empty" style={{ height }}>
        <span>{emptyMessage}</span>
      </div>
    );
  }

  const values = data.map((d) => d.value);
  const maxVal = Math.max(...values, 1);

  const paddingX = 40;
  const paddingY = 30;
  const width = 600;
  const plotWidth = width - paddingX * 2;
  const plotHeight = height - paddingY * 2;

  const barWidth = Math.min(plotWidth / data.length - 6, 28);
  const step = plotWidth / data.length;

  return (
    <div className="chart-wrapper" style={{ height }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="chart-svg"
        preserveAspectRatio="none"
        onMouseLeave={() => setHoveredIdx(null)}
      >
        {/* Background Grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
          const y = paddingY + plotHeight * (1 - pct);
          return (
            <g key={i}>
              <line
                x1={paddingX}
                y1={y}
                x2={width - paddingX}
                y2={y}
                stroke="rgba(255, 255, 255, 0.08)"
                strokeDasharray="4 4"
              />
              <text
                x={paddingX - 8}
                y={y + 4}
                textAnchor="end"
                fill="rgba(255, 255, 255, 0.4)"
                fontSize="10"
                fontFamily="monospace"
              >
                {formatValue(Math.round(maxVal * pct))}
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {data.map((d, i) => {
          const barHeight = Math.max((d.value / maxVal) * plotHeight, 2);
          const x = paddingX + i * step + (step - barWidth) / 2;
          const y = paddingY + plotHeight - barHeight;
          const isHovered = hoveredIdx === i;

          return (
            <g
              key={i}
              onMouseEnter={() => setHoveredIdx(i)}
              style={{ cursor: "pointer" }}
            >
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={isHovered ? "#fff" : color}
                rx={4}
                opacity={isHovered ? 1 : 0.85}
              />
              <rect
                x={paddingX + i * step}
                y={0}
                width={step}
                height={height}
                fill="transparent"
              />
            </g>
          );
        })}
      </svg>

      {hoveredIdx !== null && (
        <div
          className="chart-tooltip"
          style={{
            left: `${((paddingX + hoveredIdx * step + step / 2) / width) * 100}%`,
            top: `${(1 - data[hoveredIdx].value / maxVal) * 60 + 20}%`,
          }}
        >
          <div className="tooltip-date">{data[hoveredIdx].label}</div>
          <div className="tooltip-val" style={{ color }}>
            {formatValue(data[hoveredIdx].value)}
          </div>
        </div>
      )}

      <div className="chart-x-labels">
        {data.length > 0 && <span>{data[0].label}</span>}
        {data.length > 2 && (
          <span>{data[Math.floor(data.length / 2)].label}</span>
        )}
        {data.length > 1 && <span>{data[data.length - 1].label}</span>}
      </div>
    </div>
  );
}

// =============================================================================
// DONUT CHART
// =============================================================================

export interface DonutItem {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  data: DonutItem[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  emptyMessage?: string;
}

export function DonutChart({
  data,
  size = 200,
  thickness = 26,
  centerLabel,
  emptyMessage = "No data available",
}: DonutChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (total === 0 || data.length === 0) {
    return (
      <div className="donut-wrapper">
        <div className="chart-empty" style={{ width: size, height: size }}>
          <span>{emptyMessage}</span>
        </div>
      </div>
    );
  }

  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  let accumulatedOffset = 0;

  return (
    <div className="donut-container">
      <div className="donut-graphic" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth={thickness}
          />
          {/* Segments */}
          {data.map((item, i) => {
            const ratio = item.value / total;
            const strokeDasharray = `${circumference * ratio} ${circumference * (1 - ratio)}`;
            const strokeDashoffset = -accumulatedOffset;
            accumulatedOffset += circumference * ratio;

            return (
              <circle
                key={i}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="transparent"
                stroke={item.color}
                strokeWidth={thickness}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="butt"
                style={{
                  transform: "rotate(-90deg)",
                  transformOrigin: "center",
                  transition: "stroke-dashoffset 0.4s ease",
                }}
              />
            );
          })}
        </svg>

        <div className="donut-center-info">
          <span className="donut-total">{total.toLocaleString()}</span>
          <span className="donut-label">{centerLabel ?? "Total"}</span>
        </div>
      </div>

      <div className="donut-legend">
        {data.map((item, i) => {
          const pct = ((item.value / total) * 100).toFixed(1);
          return (
            <div key={i} className="donut-legend-item">
              <span
                className="legend-color-dot"
                style={{ backgroundColor: item.color }}
              />
              <span className="legend-label">{item.label}</span>
              <span className="legend-value">{item.value.toLocaleString()}</span>
              <span className="legend-pct">({pct}%)</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
