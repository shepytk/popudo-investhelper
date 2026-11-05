import Link from "next/link";

import { ResearchDataStatus } from "@/components/research-data-status";
import { researchGet } from "@/lib/research-api";

type Company = {
  id: number; name: string; ticker: string;
  exchange: string; currency_code: string;
};
type CompanyPage = { items: Company[]; total: number; limit: number; offset: number };
type Params = { q?: string; country_id?: string; sector_id?: string; page?: string };
const PAGE_SIZE = 20;

function positiveInt(input: string | undefined): number | undefined {
  if (!input || !/^[1-9]\d*$/.test(input)) return undefined;
  const value = Number(input);
  return Number.isSafeInteger(value) ? value : undefined;
}
function makeUrl(filters: Params, page: number) {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (positiveInt(filters.country_id)) params.set("country_id", filters.country_id!);
  if (positiveInt(filters.sector_id)) params.set("sector_id", filters.sector_id!);
  if (page > 1) params.set("page", String(page));
  return `/screener?${params.toString()}`;
}

export default async function Screener({ searchParams }: { searchParams: Promise<Params> }) {
  const input = await searchParams;
  const q = (input.q || "").trim().slice(0, 100);
  const country = positiveInt(input.country_id);
  const sector = positiveInt(input.sector_id);
  const requestedPage = positiveInt(input.page) || 1;
  const page = Math.min(requestedPage, 10000);
  const offset = (page - 1) * PAGE_SIZE;
  const args = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
  if (q) args.set("q", q);
  if (country) args.set("country_id", String(country));
  if (sector) args.set("sector_id", String(sector));
  const response = await researchGet<CompanyPage>(`/api/companies/page?${args.toString()}`);
  const filters = { q, country_id: country?.toString(), sector_id: sector?.toString() };
  return (
    <main id="main-content" className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-8 sm:py-10">
      <nav><Link href="/" className="underline">Home</Link></nav>
      <header>
        <h1 className="text-2xl font-semibold sm:text-3xl">Company screener</h1>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          Search verified issuer metadata, country and sector IDs. Valuation ranking is unavailable until sourced ratios exist.
        </p>
      </header>
      <form action="/screener" method="get" role="search"
        className="grid min-w-0 gap-4 rounded-xl border border-slate-300 p-4 dark:border-slate-700 sm:grid-cols-2 lg:grid-cols-4">
        <label className="block min-w-0 text-sm" htmlFor="search-query">
          <span className="font-semibold">Name or symbol</span>
          <input id="search-query" name="q" type="search" defaultValue={q} maxLength={100}
            placeholder="e.g. ASML" className="mt-1 block min-h-11 w-full min-w-0 rounded border border-slate-400 bg-transparent px-3 text-base focus-visible:outline-2" />
        </label>
        <label className="block text-sm" htmlFor="country-filter">
          <span className="font-semibold">Country ID (optional)</span>
          <input id="country-filter" name="country_id" type="number" min="1" step="1"
            defaultValue={country || ""} className="mt-1 block min-h-11 w-full rounded border border-slate-400 bg-transparent px-3 text-base focus-visible:outline-2" />
        </label>
        <label className="block text-sm" htmlFor="sector-filter">
          <span className="font-semibold">Sector ID (optional)</span>
          <input id="sector-filter" name="sector_id" type="number" min="1" step="1"
            defaultValue={sector || ""} className="mt-1 block min-h-11 w-full rounded border border-slate-400 bg-transparent px-3 text-base focus-visible:outline-2" />
        </label>
        <div className="flex items-end gap-2">
          <button type="submit" className="min-h-11 flex-1 rounded bg-slate-900 px-4 text-white focus-visible:outline-2 focus-visible:outline-offset-2 dark:bg-slate-100 dark:text-slate-900">Apply filters</button>
          <Link href="/screener" className="inline-flex min-h-11 items-center rounded border border-slate-500 px-3 underline">Reset</Link>
        </div>
      </form>
      {response.status === "error" ? (
        <ResearchDataStatus subject="Company screening" code={response.code} message={response.message} />
      ) : response.data.items.length === 0 ? (
        <ResearchDataStatus subject="Company screening" code="empty" message="Try fewer filters or a different name." />
      ) : (
        <section aria-labelledby="results-title">
          <h2 id="results-title" className="text-lg font-semibold">Results</h2>
          <p role="status" className="mt-1 text-sm">{response.data.total} matching issuers. Page {page}.</p>
          <div className="mt-3 overflow-x-auto rounded-lg border border-slate-300 dark:border-slate-700" role="region" tabIndex={0} aria-label="Scrollable company search results">
            <table className="min-w-[580px] w-full text-left text-sm">
              <caption className="sr-only">Issuer matches with display ticker, exchange and currency</caption>
              <thead><tr className="border-b border-slate-300 dark:border-slate-700">
                <th scope="col" className="p-3">Company</th><th scope="col" className="p-3">Display ticker</th>
                <th scope="col" className="p-3">Exchange</th><th scope="col" className="p-3">Currency</th>
              </tr></thead>
              <tbody>{response.data.items.map((issuer) => (
                <tr key={issuer.id} className="border-b border-slate-200 dark:border-slate-800">
                  <td className="p-3"><Link href={`/companies/${issuer.id}`} className="underline underline-offset-2 focus-visible:outline-2">{issuer.name}</Link></td>
                  <td className="p-3">{issuer.ticker}</td><td className="p-3">{issuer.exchange}</td><td className="p-3">{issuer.currency_code}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <nav aria-label="Screening pagination" className="mt-4 flex flex-wrap items-center justify-between gap-4">
            {page > 1
              ? <Link className="min-h-11 rounded border border-slate-500 px-4 py-2 underline" href={makeUrl(filters, page - 1)}>Previous page</Link>
              : <span>First page</span>}
            {offset + response.data.items.length < response.data.total
              ? <Link className="min-h-11 rounded border border-slate-500 px-4 py-2 underline" href={makeUrl(filters, page + 1)}>Next page</Link>
              : <span>End of results</span>}
          </nav>
        </section>
      )}
    </main>
  );
}
