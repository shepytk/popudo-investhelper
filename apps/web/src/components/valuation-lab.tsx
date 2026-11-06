"use client";

import { useMemo, useState } from "react";

import { calculateDcf, DCF_MODEL_VERSION } from "@/lib/valuation/model";
import { parseValuationForm, type ValuationForm } from "@/lib/valuation/input";
import { buildScenarios, buildSensitivity, enterpriseValueShareFromTerminal, marginOfSafety } from "@/lib/valuation/scenarios";

const EMPTY: ValuationForm = {
  fcf: "", debt: "", shares: "", growth: "", discount: "", terminal: "",
  spread: "", years: "5", price: "", currency: "EUR",
};
const DISCOUNT_OFFSETS = [-0.02, -0.01, 0, 0.01, 0.02] as const;
const TERMINAL_OFFSETS = [-0.01, -0.005, 0, 0.005, 0.01] as const;
const LABELS: { key: keyof ValuationForm; label: string; hint: string; required?: boolean }[] = [
  { key: "fcf", label: "Starting annual free cash flow", hint: "Millions of currency units", required: true },
  { key: "debt", label: "Net debt", hint: "Millions; negative for net cash", required: true },
  { key: "shares", label: "Diluted shares outstanding", hint: "Millions of shares", required: true },
  { key: "growth", label: "Annual FCF growth", hint: "Percent per year", required: true },
  { key: "discount", label: "Discount rate", hint: "Percent per year", required: true },
  { key: "terminal", label: "Terminal growth", hint: "Percent per year", required: true },
  { key: "spread", label: "Bear/bull growth difference", hint: "Percentage points from base case", required: true },
  { key: "price", label: "Optional comparison share price", hint: "Same currency, per diluted share" },
];
const format = (n: number, places = 2) => new Intl.NumberFormat("en", { maximumFractionDigits: places }).format(n);
const percent = (n: number) => `${format(n * 100, 2)}%`;

export function ValuationLab() {
  const [form, setForm] = useState<ValuationForm>(EMPTY);
  const [show, setShow] = useState(false);
  const [run, setRun] = useState<{ id: string; generatedAt: string } | null>(null);
  const parsed = useMemo(() => parseValuationForm(form), [form]);
  const base = parsed.status === "ready" ? calculateDcf(parsed.input) : null;
  const valid = parsed.status === "ready" && base?.status === "ok";
  const scenarios = valid ? buildScenarios(parsed.input, parsed.spread) : [];
  const sensitivity = valid ? buildSensitivity(parsed.input, DISCOUNT_OFFSETS, TERMINAL_OFFSETS) : [];
  const result = valid && base?.status === "ok" ? base.result : null;
  const safety = result && parsed.status === "ready" && parsed.price !== null
    ? marginOfSafety(result.intrinsicValuePerShare, parsed.price) : null;
  const plotted = scenarios.filter((scenario) => scenario.outcome.status === "ok");
  const maxFcf = Math.max(1, ...plotted.flatMap((scenario) =>
    scenario.outcome.status === "ok" ? scenario.outcome.result.years.map((year) => year.projectedFcfMillions) : []));
  const height = (fcf: number) => 220 - (fcf / maxFcf) * 175;
  const x = (year: number, count: number) => 52 + (year / count) * 590;

  function change(key: keyof ValuationForm, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
    setShow(false);
    setRun(null);
  }

  return (
    <section aria-labelledby="valuation-lab-title" className="space-y-6">
      <div>
        <h2 id="valuation-lab-title" className="text-2xl font-semibold">DCF valuation scenario lab</h2>
        <p className="mt-2 text-sm">Enter your own assumptions to explore valuation methodology. All inputs are hypothetical and stay in this browser session. Nothing is imported from company records.</p>
      </div>
      <form onSubmit={(event) => { event.preventDefault(); setRun({ id: crypto.randomUUID(), generatedAt: new Date().toISOString() }); setShow(true); }} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {LABELS.map((field) => (
            <label key={field.key} className="block text-sm">
              <span className="block font-semibold">{field.label}{field.required ? " *" : ""}</span>
              <span className="block text-xs text-slate-700 dark:text-slate-300">{field.hint}</span>
              <input type="number" inputMode="decimal" step="any" required={field.required}
                value={form[field.key]} onChange={(event) => change(field.key, event.target.value)}
                className="mt-1 block min-h-11 w-full rounded border border-slate-500 bg-transparent px-3 text-base focus-visible:outline-2 focus-visible:outline-offset-2" />
            </label>
          ))}
          <label className="block text-sm">
            <span className="block font-semibold">Projection horizon</span>
            <select value={form.years} onChange={(event) => change("years", event.target.value)}
              className="mt-1 block min-h-11 w-full rounded border border-slate-500 bg-transparent px-3 text-base">
              <option value="5">5 years</option><option value="10">10 years</option>
            </select>
          </label>
          <label className="block text-sm">
            <span className="block font-semibold">Currency for entered amounts</span>
            <select value={form.currency} onChange={(event) => change("currency", event.target.value)}
              className="mt-1 block min-h-11 w-full rounded border border-slate-500 bg-transparent px-3 text-base">
              <option value="EUR">EUR</option><option value="USD">USD</option><option value="GBP">GBP</option>
            </select>
          </label>
        </div>
        <div className="flex flex-wrap gap-3">
          <button type="submit" className="min-h-11 rounded bg-slate-900 px-5 py-2 text-white focus-visible:outline-2 focus-visible:outline-offset-2 dark:bg-slate-100 dark:text-slate-900">Calculate scenarios</button>
          <button type="button" onClick={() => { setForm(EMPTY); setShow(false); setRun(null); }}
            className="min-h-11 rounded border border-slate-500 px-5 py-2 focus-visible:outline-2 focus-visible:outline-offset-2">Clear assumptions</button>
        </div>
      </form>
      {show && !valid && <p role="alert" className="rounded border border-amber-600 p-3 text-sm">
        {parsed.status === "incomplete" ? parsed.reason : base?.status === "invalid" ? base.reason : "Assumptions cannot be evaluated."}
      </p>}
      {show && valid && result && parsed.status === "ready" && (
        <div className="space-y-6" role="region" aria-label="Hypothetical valuation results">
          <div className="rounded border border-slate-500 p-4">
            <p className="font-semibold">Hypothetical intrinsic value per diluted share</p>
            <p className="mt-1 text-2xl font-semibold">{format(result.intrinsicValuePerShare)} {form.currency}</p>
            <p className="mt-2 text-sm">Enterprise value: {format(result.enterpriseValueMillions)} million {form.currency}.
              Equity value: {format(result.equityValueMillions)} million {form.currency}.</p>
            <p className="mt-2 text-sm">Present value of terminal cash flows: {percent(enterpriseValueShareFromTerminal(result))} of enterprise value.</p>
            {safety !== null && <p className="mt-2 text-sm">Margin of safety versus entered price: {percent(safety)}.</p>}
            <p className="mt-2 text-xs">Not a company valuation or investment recommendation. This result uses only your manually entered assumptions.</p>
            {run && <p className="mt-2 break-all text-xs">Calculation: {DCF_MODEL_VERSION} · Run: {run.id} · Input source: manual · Generated: {run.generatedAt}. This run identifier is browser-local and is not persisted.</p>}
          </div>
          <figure className="space-y-2">
            <h3 className="text-lg font-semibold">Projected annual free cash flow by scenario</h3>
            <div className="overflow-x-auto rounded border border-slate-300 p-2 dark:border-slate-700" role="region" tabIndex={0} aria-label="Scrollable hypothetical cash flow chart">
              <svg viewBox="0 0 680 265" className="min-w-[360px] w-full" role="img" aria-labelledby="scenario-chart-title scenario-chart-desc">
                <title id="scenario-chart-title">Bear, base, bull projected free cash flow</title>
                <desc id="scenario-chart-desc">Hypothetical annual cash flows based on entered growth assumptions. Exact values appear in the table immediately below.</desc>
                <line x1="52" y1="220" x2="645" y2="220" stroke="currentColor" opacity=".5"/>
                {plotted.map((scenario, index) => {
                  if (scenario.outcome.status !== "ok") return null;
                  const color = ["#b45309", "#2563eb", "#059669"][index];
                  const years = scenario.outcome.result.years;
                  return <polyline key={scenario.label} fill="none" stroke={color} strokeWidth="3"
                    points={years.map((year) => `${x(year.year, years.length)},${height(year.projectedFcfMillions)}`).join(" ")} />;
                })}
                {result.years.map((year) => <text key={year.year} x={x(year.year, result.years.length)}
                  y="240" textAnchor="middle" fill="currentColor" fontSize="12">{year.year}</text>)}
                <text x="52" y="255" fontSize="11" fill="currentColor">Forecast years; FCF in millions of {form.currency}</text>
              </svg>
            </div>
            <ul className="flex flex-wrap gap-4 text-sm">
              {plotted.map((scenario, index) => <li key={scenario.label}>
                <span aria-hidden="true" className="mr-2 inline-block h-3 w-3 rounded-sm"
                  style={{ backgroundColor: ["#b45309", "#2563eb", "#059669"][index] }} />
                {scenario.label} ({percent(scenario.growthRate)} growth)
              </li>)}
            </ul>
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Cash flow projections data table">
              <table className="min-w-[450px] w-full text-left text-sm">
                <caption className="py-2 text-left">Exact projected free cash flow in millions of {form.currency}; hypothetical</caption>
                <thead><tr><th className="p-2" scope="col">Year</th>
                  {scenarios.map((scenario) => <th className="p-2" scope="col" key={scenario.label}>{scenario.label}</th>)}
                </tr></thead>
                <tbody>{result.years.map((year, index) => <tr key={year.year} className="border-t border-slate-300 dark:border-slate-700">
                  <th className="p-2" scope="row">{year.year}</th>
                  {scenarios.map((scenario) => <td key={scenario.label} className="p-2">
                    {scenario.outcome.status === "ok" ? format(scenario.outcome.result.years[index].projectedFcfMillions, 4) : "Not computable"}
                  </td>)}
                </tr>)}</tbody>
              </table>
            </div>
          </figure>
          <section aria-labelledby="scenario-values-title">
            <h3 id="scenario-values-title" className="text-lg font-semibold">Bear / base / bull intrinsic values</h3>
            <div className="mt-2 grid gap-3 sm:grid-cols-3">
              {scenarios.map((scenario) => <div key={scenario.label} className="rounded border border-slate-300 p-3 dark:border-slate-700">
                <p className="font-semibold">{scenario.label}</p>
                <p className="text-sm">FCF growth {percent(scenario.growthRate)}</p>
                <p className="mt-1 text-lg">{scenario.outcome.status === "ok"
                  ? `${format(scenario.outcome.result.intrinsicValuePerShare)} ${form.currency}`
                  : "Not computable"}</p>
              </div>)}
            </div>
          </section>
          <section aria-labelledby="sensitivity-title">
            <h3 id="sensitivity-title" className="text-lg font-semibold">Sensitivity to discount rate and terminal growth</h3>
            <p className="mt-1 text-sm">Intrinsic value per share ({form.currency}); rows vary the discount rate, columns vary terminal growth. Invalid combinations are not computed.</p>
            <div className="mt-3 overflow-x-auto" role="region" tabIndex={0} aria-label="Scrollable sensitivity table">
              <table className="min-w-[580px] w-full text-sm text-right">
                <caption className="py-2 text-left">Hypothetical five-by-five DCF sensitivity matrix</caption>
                <thead><tr>
                  <th scope="col" className="p-2 text-left">Discount / terminal</th>
                  {TERMINAL_OFFSETS.map((offset) => <th scope="col" className="p-2" key={offset}>{percent(parsed.input.terminalGrowthRate + offset)}</th>)}
                </tr></thead>
                <tbody>{DISCOUNT_OFFSETS.map((offset, row) => <tr key={offset} className="border-t border-slate-300 dark:border-slate-700">
                  <th scope="row" className="p-2 text-left">{percent(parsed.input.discountRate + offset)}</th>
                  {TERMINAL_OFFSETS.map((shift, col) => {
                    const cell = sensitivity[row * TERMINAL_OFFSETS.length + col];
                    return <td className="p-2" key={shift}>{cell.outcome.status === "ok"
                      ? format(cell.outcome.result.intrinsicValuePerShare) : "N/A"}</td>;
                  })}
                </tr>)}</tbody>
              </table>
            </div>
          </section>
          <details className="rounded border border-slate-300 p-4 text-sm dark:border-slate-700">
            <summary className="cursor-pointer font-semibold">Formula and assumptions audit</summary>
            <p className="mt-3">FCF(t) = starting FCF × (1 + growth)^t. Present value = FCF(t) ÷ (1 + discount rate)^t.</p>
            <p className="mt-2">Terminal value = FCF(last year) × (1 + terminal growth) ÷ (discount rate − terminal growth).</p>
            <p className="mt-2">Enterprise value = sum of discounted FCF + discounted terminal value.
              Equity value = enterprise value − net debt. Intrinsic value per share = equity value ÷ diluted shares.</p>
            <p className="mt-2">Bear/bull scenarios change only the annual FCF growth rate. Sensitivity varies only discount and terminal growth rates.
              This simplified DCF omits taxes, mid-year discounting and capital-structure adjustments not captured in net debt.</p>
          </details>
        </div>
      )}
    </section>
  );
}
