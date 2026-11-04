import Link from "next/link";
import { researchGet } from "@/lib/research-api";

type Company = {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
  currency_code: string;
};
type CompanyPage = { items: Company[]; total: number; limit: number; offset: number };
type Search = { q?: string; country_id?: string; sector_id?: string; offset?: string };

function positiveInteger(value?: string): string | null {
  if (!value || !/^[0-9]+$/.test(value)) return null;
  const numeric = Number(value);
  return Number.isSafeInteger(numeric) && numeric > 0 ? String(numeric) : null;
}

export default async function StockScreen({ searchParams }: { searchParams: Promise<Search> }) {
  const params = await searchParams;
  const query = (params.q || "").slice(0, 100);
  const countryId = positiveInteger(params.country_id);
  const sectorId = positiveInteger(params.sector_id);
  const offset = params.offset && /^[0-9]+$/.test(params.offset)
    ? Math.min(Number(params.offset) || 0, 1000000) : 0;
  const filters = new URLSearchParams({ limit: "25", offset: String(offset) });
  if (query) filters.set("q", query);
  if (countryId) filters.set("country_id", countryId);
  if (sectorId) filters.set("sector_id", sectorId);
  const response = await researchGet<CompanyPage>(`/api/companies/page?${filters}`);

  function pageHref(nextOffset: number): string {
    const changed = new URLSearchParams(filters);
    changed.set("offset", String(nextOffset));
    return `/screen?${changed.toString()}`;
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-8 sm:py-10">
      <Link href="/" className="inline-block rounded underline underline-offset-2 focus-visible:outline-2">Home</Link>
      <header>
        <h1 className="text-2xl font-semibold sm:text-3xl">Company screening</h1>
        <p className="mt-2 max-w-prose text-sm text-slate-600 dark:text-slate-300">
          Search and filter issuer metadata. Being listed here does not imply independently
          verified market prices or a recommendation.
        </p>
      </header>
      <form action="/screen" method="get" role="search"
        className="grid gap-3 rounded-lg border border-slate-300 p-4 dark:border-slate-700 sm:grid-cols-3">
        <label className="space-y-1 text-sm">
          <span className="block font-semibold">Company name or ticker</span>
          <input name="q" defaultValue={query} maxLength={100}
            className="w-full rounded border border-slate-400 bg-transparent px-3 py-2"
            placeholder="e.g. ASML" />
        </label>
        <label className="space-y-1 text-sm">
          <span className="block font-semibold">Country ID (optional)</span>
          <input name="country_id" defaultValue={countryId || ""} inputMode="numeric"
            pattern="[0-9]*" className="w-full rounded border border-slate-400 bg-transparent px-3 py-2"
            placeholder="All countries" />
        </label>
        <label className="space-y-1 text-sm">
          <span className="block font-semibold">Sector ID (optional)</span>
          <input name="sector_id" defaultValue={sectorId || ""} inputMode="numeric"
            pattern="[0-9]*" className="w-full rounded border border-slate-400 bg-transparent px-3 py-2"
            placeholder="All sectors" />
        </label>
        <button type="submit"
          className="rounded bg-slate-950 px-5 py-2 font-medium text-white focus-visible:outline-2 focus-visible:outline-offset-2 dark:bg-white dark:text-slate-950 sm:col-span-3 sm:justify-self-start">
          Apply filters
        </button>
      </form>
      <section aria-labelledby="results-heading">
        <h2 id="results-heading" className="text-xl font-semibold">Matching companies</h2>
        {response.status === "error" ? (
          <p role="alert" className="mt-3">Company search is temporarily unavailable. No empty result was assumed.</p>
        ) : response.data.total === 0 ? (
          <p role="status" className="mt-3">No companies match those filters. Try a broader ticker or country.</p>
        ) : (
          <>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300" role="status">
              {response.data.total} matching issuers; showing {response.data.items.length} from result {offset + 1}.
            </p>
            <ul className="mt-4 grid gap-3 sm:grid-cols-2">
              {response.data.items.map((company) => (
                <li key={company.id} className="rounded-lg border border-slate-300 p-4 dark:border-slate-700">
                  <h3 className="font-semibold">
                    <Link className="rounded underline underline-offset-2 focus-visible:outline-2"
                      href={`/companies/${company.id}`}>{company.name}</Link>
                  </h3>
                  <p className="mt-2 text-sm">{company.ticker} · {company.exchange} · {company.currency_code}</p>
                  <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">Issuer metadata; verify listing identity on company page.</p>
                </li>
              ))}
            </ul>
            <nav aria-label="Screening result pages" className="mt-5 flex flex-wrap gap-3">
              {offset > 0 && <Link className="rounded border px-4 py-2 underline focus-visible:outline-2"
                href={pageHref(Math.max(0, offset - 25))}>Previous results</Link>}
              {offset + response.data.items.length < response.data.total &&
                <Link className="rounded border px-4 py-2 underline focus-visible:outline-2"
                  href={pageHref(offset + 25)}>Next results</Link>}
            </nav>
          </>
        )}
      </section>
    </main>
  );
}
