/** Accessible no-dependency chart with its exact tabular source values. */
export type ChartFinancial = {
  fiscal_year: number;
  period_type: string;
  reporting_currency: string | null;
  revenue: string;
  net_income: string;
  free_cash_flow: string;
  source: string;
  period_end_date: string;
};

const METRICS = [
  { key: "revenue", name: "Revenue", stroke: "#2563eb" },
  { key: "net_income", name: "Net income", stroke: "#059669" },
  { key: "free_cash_flow", name: "Free cash flow", stroke: "#b45309" },
] as const;

function numeric(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function FinancialTrend({ data }: { data: ChartFinancial[] }) {
  const annual = [...data]
    .filter((row) => row.period_type === "annual")
    .sort((a, b) => a.fiscal_year - b.fiscal_year)
    .slice(-7);
  const currencies = new Set(annual.map((row) => row.reporting_currency));
  if (annual.length < 2 || currencies.size !== 1 || currencies.has(null)) {
    return (
      <p className="text-sm text-slate-600 dark:text-slate-300">
        A multi-year trend requires at least two comparable annual reports in the same reporting currency.
        Missing or mixed-currency observations are not plotted as zero.
      </p>
    );
  }
  const numbers = annual.flatMap((row) => METRICS
    .map((metric) => numeric(row[metric.key]))
    .filter((n): n is number => n !== null));
  if (numbers.length !== annual.length * METRICS.length) {
    return <p className="text-sm">A verified financial trend cannot be drawn because some amounts are missing.</p>;
  }
  const low = Math.min(0, ...numbers);
  const high = Math.max(0, ...numbers);
  const span = Math.max(high - low, 1);
  const x = (index: number) => 65 + (index / Math.max(annual.length - 1, 1)) * 595;
  const y = (number: number) => 220 - ((number - low) / span) * 175;
  const format = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
  const currency = annual[0].reporting_currency;
  return (
    <figure className="space-y-3" aria-labelledby="financial-trend-heading">
      <h3 id="financial-trend-heading" className="text-lg font-semibold">Annual financial trends</h3>
      <div className="overflow-x-auto rounded border border-slate-200 p-2 dark:border-slate-700">
        <svg viewBox="0 0 700 268" className="min-w-[430px] w-full" role="img"
          aria-labelledby="financial-chart-title financial-chart-desc">
          <title id="financial-chart-title">Revenue, net income and free cash flow by fiscal year</title>
          <desc id="financial-chart-desc">
            {METRICS.map((metric) => `${metric.name}: ${annual.map((row) => `${row.fiscal_year} ${row[metric.key]}`).join(", ")}.`).join(" ")}
            Exact source values appear in the table below.
          </desc>
          {[0, 0.5, 1].map((t) => {
            const value = low + t * span;
            return <g key={t}>
              <line x1="65" y1={y(value)} x2="665" y2={y(value)} stroke="currentColor" opacity=".12"/>
              <text x="58" y={y(value) + 4} textAnchor="end" fontSize="11" fill="currentColor">
                {format.format(value)}
              </text>
            </g>;
          })}
          {METRICS.map((metric) => (
            <g key={metric.key}>
              <polyline fill="none" stroke={metric.stroke} strokeWidth="3" strokeLinejoin="round"
                points={annual.map((row, index) => `${x(index)},${y(Number(row[metric.key]))}`).join(" ")} />
              {annual.map((row, index) => (
                <circle key={row.fiscal_year} cx={x(index)} cy={y(Number(row[metric.key]))}
                  r="4" stroke={metric.stroke} fill="white">
                  <title>{metric.name}, {row.fiscal_year}: {row[metric.key]} {currency}</title>
                </circle>
              ))}
            </g>
          ))}
          {annual.map((row, index) => (
            <text key={row.fiscal_year} x={x(index)} y="252" fontSize="12" textAnchor="middle" fill="currentColor">
              {row.fiscal_year}
            </text>
          ))}
        </svg>
      </div>
      <ul className="flex flex-wrap gap-4 text-sm" aria-label="Chart series legend">
        {METRICS.map((metric) => <li key={metric.key} className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: metric.stroke }}/>
          {metric.name}
        </li>)}
      </ul>
      <p className="text-xs text-slate-600 dark:text-slate-300">
        Reporting currency: {currency}. Exact amounts and filing periods are in the accessible fundamentals table.
        These are source-reported facts, not forecasts.
      </p>
    </figure>
  );
}
