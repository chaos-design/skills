import { useId } from "react";

const WIDTH = 96;
const HEIGHT = 24;
const PAD = 2;

/**
 * Area + line sparkline for the 8 weekly activity buckets. Geometry mirrors
 * the reference directory: a smoothed line with a fading gradient fill,
 * colored with currentColor so the row hover state can brighten it.
 */
export function ActivitySparkline({ values, label }: { values: number[]; label: string }) {
  // useId() contains colons, which are awkward inside url(#...) references.
  const gradientId = `sparkline-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const max = Math.max(...values, 1);
  const points = values.map((value, index) => {
    const x = PAD + (index * (WIDTH - 2 * PAD)) / Math.max(values.length - 1, 1);
    const y = HEIGHT - PAD - (value / max) * (HEIGHT - 2 * PAD);
    return [x, y] as const;
  });

  const line = smoothPath(points);
  const area = `${line} L ${points[points.length - 1][0].toFixed(1)},${HEIGHT - PAD} L ${points[0][0].toFixed(1)},${HEIGHT - PAD} Z`;

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label={label}
      className="h-full w-full overflow-visible text-ds-gray-600 opacity-65 transition-[color,opacity] duration-200 ease-out group-hover/sparkline:text-ds-gray-300 group-hover/sparkline:opacity-100"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2={HEIGHT} gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.22" />
          <stop offset="55%" stopColor="currentColor" stopOpacity="0.085" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path
        d={line}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Catmull-Rom spline through the points, emitted as cubic beziers. */
function smoothPath(points: readonly (readonly [number, number])[]): string {
  if (points.length < 2) return "";
  const at = (index: number) => points[Math.min(Math.max(index, 0), points.length - 1)];
  let d = `M${points[0][0].toFixed(1)},${points[0][1].toFixed(1)}`;
  for (let i = 0; i < points.length - 1; i += 1) {
    const p0 = at(i - 1);
    const p1 = at(i);
    const p2 = at(i + 1);
    const p3 = at(i + 2);
    const c1x = p1[0] + (p2[0] - p0[0]) / 6;
    const c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6;
    const c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}
