import Link from "next/link";

import { FinancialTrend } from "@/components/financial-trend";
import { researchGet } from "@/lib/research-api";
import { InsightPanel } from "./insight-panel";

type Company = {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
  description: string;
  currency_code: string;
};

type Financial = {
  fiscal_year: number;
  fiscal_quarter?: number | null;
  period_type: string;
  period_end_date: string;
  revenue: string;
  net_income: string;
  free_cash_flow: string;
  operating_cash_flow: string;
  capital_expenditure: string;
  total_debt: string;
  cash_and_equivalents: string;
  source: string;
  source_url: string | null;
  reporting_currency: string | null;
  amount_unit: string | null;
  published_date: string | null;
  retrieved_at: string | null;
};

type Listing = {
  id: number;
  mic: string;
  symbol: string;
  currency_code: string;
  is_adr: boolean;
  verified: boolean;
  valid_from: string;
  valid_to: string | null;
};

type Quote = {
  date: string;
  close: string;
  currency_code: string;
  provider: string;
  mic: string;
  symbol: string;
  source_url: string;
  retrieved_at: string;
};

const cell = "whitespace-nowrap px-4 py-3 text-left";
const heading = `${cell} font-semibold`;

function sourceDate(date: string | null) {
  if (!date) return "Unknown";
  const parsed = new Date(date);
  return Number.isNaN(parsed.getTime()) ? "Invalid date" : parsed.toISOString().slice(0, 10);
}

function annualStaleness(financial: Financial): string {
  const end = Date.parse(financial.period_end_date + "T00:00:00Z");
  if (!Number.isFinite(end)) return "Reporting date unavailable";
  return (Date.now() - end) / 86400000 > 550
    ? "Historical report — outside current-data freshness window"
    : "Within annual reporting freshness window";
}

function sourceLink(label: string, url: string | null) {
  if (!url?.startsWith("https://")) return <span>{label} (source URL unavailable)</span>;
  return <a href={url} target="_blank" rel="noopener noreferrer"
    className="underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2">
    {label}<span className="sr-only"> (opens in a new tab)</span>
  </a>;
}

export default async function CompanyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const companyId = Number(id);
  if (!Number.isSafeInteger(companyId) || companyId <= 0) {
    return <main className="mx-auto max-w-5xl p-4 sm:p-8"><h1 className="text-2xl font-semibold">Invalid company identifier</h1></main>;
  }
  const [company, statements, listings, quotes] = await Promise.all([
    researchGet<Company>(`/api/companies/${companyId}`),
    researchGet<Financial[]>(`/api/companies/${companyId}/financials`),
    researchGet<Listing[]>(`/api/companies/${companyId}/listings`),
    researchGet<Quote[]>(`/api/companies/${companyId}/quotes`),
  ]);
  if (company.status === "error") {
    return (
      <main className="mx-auto max-w-5xl p-4 sm:p-8" role="main">
        <Link href="/sectors" className="underline">Back to sectors</Link>
        <h1 className="mt-4 text-2xl font-semibold">
          {company.code === "company_not_found" ? "Company not found" : "Company data unavailable"}
        </h1>
        <p role="alert" className="mt-3 text-sm">{company.message}</p>
      </main>
    );
  }
  const issuer = company.data;
  const financials = statements.status === "ok" ? statements.data : [];
  const annual = financials.filter((record) => record.period_type === "annual")
    .sort((a, b) => b.fiscal_year - a.fiscal_year);
  const listingRows = listings.status === "ok" ? listings.data : [];
  return (
    <main id="main-content" className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-8 sm:py-10">
      <Link href="/sectors" className="inline-block rounded underline underline-offset-2 focus-visible:outline-2">
        Back to sectors
      </Link>
      <header className="rounded-xl border border-slate-300 p-4 dark:border-slate-700 sm:p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-300">Company issuer</p>
        <h1 className="mt-1 text-2xl font-semibold sm:text-3xl">{issuer.name}</h1>
        <p className="mt-2 text-sm">Legacy display symbol: {issuer.ticker} · {issuer.exchange}</p>
        <p className="mt-3 max-w-3xl text-sm">{issuer.description || "Issuer description not available."}</p>
        <p className="mt-3 text-xs text-slate-600 dark:text-slate-300">
          A company may have multiple listings, share classes and trading currencies. Verify the instrument below.
        </p>
      </header>

      <section aria-labelledby="listings-heading" className="rounded-xl border border-slate-300 p-4 dark:border-slate-700 sm:p-6">
        <h2 id="listings-heading" className="text-xl font-semibold">Verified exchange listings</h2>
        {listings.status === "error" ? (
          <p role="status" className="mt-3 text-sm">Listings temporarily unavailable. No exchange identity assumed.</p>
        ) : listingRows.length === 0 ? (
          <p role="status" className="mt-3 text-sm">No independently verified listing or ADR mapping has been imported yet.</p>
        ) : (
          <div className="mt-3 overflow-x-auto" tabIndex={0} role="region" aria-label="Exchange listings, scrollable on narrow screens">
            <table className="min-w-[520px] w-full text-sm">
              <caption className="sr-only">Security symbols by exchange, currency and instrument type</caption>
              <thead><tr>
                <th scope="col" className={heading}>Symbol</th>
                <th scope="col" className={heading}>Exchange MIC</th>
                <th scope="col" className={heading}>Trading currency</th>
                <th scope="col" className={heading}>Instrument</th>
                <th scope="col" className={heading}>Effective from</th>
              </tr></thead>
              <tbody>{listingRows.map((row) => <tr key={row.id} className="border-t border-slate-200 dark:border-slate-700">
                <td className={cell}>{row.symbol}</td>
                <td className={cell}>{row.mic}</td>
                <td className={cell}>{row.currency_code}</td>
                <td className={cell}>{row.is_adr ? "ADR" : "Local / non-ADR listing"}</td>
                <td className={cell}>{row.valid_from}</td>
              </tr>)}</tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-labelledby="quote-heading" className="rounded-xl border border-slate-300 p-4 dark:border-slate-700 sm:p-6">
        <h2 id="quote-heading" className="text-xl font-semibold">Market quotations</h2>
        {quotes.status === "error" ? (
          <p role="status" className="mt-3 text-sm">
            {quotes.code === "stale_data"
              ? "Only stale quotations are available; prices have been withheld."
              : quotes.code === "missing_data"
                ? "No source-verified quotations have been imported."
                : "Market price service unavailable — not reported as a zero price."}
          </p>
        ) : quotes.data.length === 0 ? (
          <p className="mt-3 text-sm">No sourced quote observations.</p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {quotes.data.slice(0, 5).map((quote) => <li key={`${quote.mic}-${quote.symbol}-${quote.date}`}>
              <strong>{quote.symbol} · {quote.mic}</strong>: {quote.close} {quote.currency_code}
              {" "}on {quote.date}; {sourceLink(quote.provider, quote.source_url)}
              <span className="text-slate-600 dark:text-slate-300"> · fetched {sourceDate(quote.retrieved_at)}</span>
            </li>)}
          </ul>
        )}
      </section>

      <section aria-labelledby="fundamentals-heading" className="rounded-xl border border-slate-300 p-4 dark:border-slate-700 sm:p-6">
        <h2 id="fundamentals-heading" className="text-xl font-semibold">Verified fundamentals</h2>
        {statements.status === "error" ? (
          <p role="alert" className="mt-3 text-sm">
            Financial statement service unavailable. Amounts have not been replaced with zeroes.
          </p>
        ) : annual.length === 0 ? (
          <p role="status" className="mt-3 text-sm">
            No complete, verified annual statements are available. Missing data, unit conversions,
            financial reconciliations or source checks may be outstanding.
          </p>
        ) : (
          <div className="mt-4 space-y-6">
            <FinancialTrend data={annual}/>
            <div className="max-w-full overflow-x-auto rounded border border-slate-200 dark:border-slate-700"
              tabIndex={0} role="region" aria-label="Annual financial statements, horizontally scrollable">
              <table className="min-w-[930px] w-full text-sm">
                <caption className="px-4 py-2 text-left text-sm">
                  Original reported amounts (not forecasts). Values retain source precision; reporting currencies may differ.
                </caption>
                <thead><tr className="border-y border-slate-200 dark:border-slate-700">
                  <th scope="col" className={heading}>Fiscal year</th>
                  <th scope="col" className={heading}>Currency / unit</th>
                  <th scope="col" className={heading}>Revenue</th>
                  <th scope="col" className={heading}>Net income</th>
                  <th scope="col" className={heading}>Operating cash flow</th>
                  <th scope="col" className={heading}>Capital expenditure</th>
                  <th scope="col" className={heading}>Free cash flow</th>
                  <th scope="col" className={heading}>Net debt inputs</th>
                  <th scope="col" className={heading}>Source / freshness</th>
                </tr></thead>
                <tbody>{annual.map((record) => (
                  <tr key={`${record.fiscal_year}-${record.period_end_date}`}
                    className="border-t border-slate-200 align-top dark:border-slate-700">
                    <td className={cell}>{record.fiscal_year}<span className="block text-xs">{record.period_end_date}</span></td>
                    <td className={cell}>{record.reporting_currency || "Unknown"} / {record.amount_unit || "Unknown"}</td>
                    <td className={cell}>{record.revenue}</td>
                    <td className={cell}>{record.net_income}</td>
                    <td className={cell}>{record.operating_cash_flow}</td>
                    <td className={cell}>{record.capital_expenditure}</td>
                    <td className={cell}>{record.free_cash_flow}</td>
                    <td className={cell}>Debt: {record.total_debt}<span className="block">Cash: {record.cash_and_equivalents}</span></td>
                    <td className={`${cell} min-w-[220px]`}>
                      {sourceLink(record.source, record.source_url)}
                      <span className="block">Filed: {sourceDate(record.published_date)}</span>
                      <span className="block">Retrieved: {sourceDate(record.retrieved_at)}</span>
                      <span className="mt-1 block text-xs">{annualStaleness(record)}</span>
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            <details className="rounded bg-slate-100 p-3 text-sm dark:bg-slate-900">
              <summary className="cursor-pointer font-medium">Calculation definitions and limitations</summary>
              <dl className="mt-2 space-y-2">
                <div><dt className="font-semibold">Free cash flow (FCF)</dt>
                  <dd>Operating cash flow minus positive capital expenditure. The API verifies reconciliation against each sourced statement.</dd></div>
                <div><dt className="font-semibold">Net debt</dt>
                  <dd>Total debt minus cash and equivalents. Inputs are displayed separately above.</dd></div>
                <div><dt className="font-semibold">Price/earnings, enterprise value and DCF</dt>
                  <dd>Not computable until verified share count, instrument-level market prices, adjustments and valuation assumptions are available. No implicit zero or unverified price target is shown.</dd></div>
              </dl>
            </details>
          </div>
        )}
      </section>

      <InsightPanel companyId={issuer.id}/>
    </main>
  );
}
