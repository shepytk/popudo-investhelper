import Link from "next/link";

import { ResearchDataStatus } from "@/components/research-data-status";
import { researchGet } from "@/lib/research-api";

type Company = { id: number; name: string; ticker: string };

type SectorWithCompanies = {
  id: number;
  name: string;
  description: string;
  companies: Company[];
};

export default async function SectorsPage() {
  const response = await researchGet<SectorWithCompanies[]>("/api/sectors/with-companies");
  return (
    <main id="main-content" className="mx-auto max-w-6xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="max-w-2xl">
        <h1 className="text-2xl font-semibold sm:text-3xl">Research by sector</h1>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
          Browse available issuers. Symbols are identifiers for discovery, not independently verified trading instruments.
        </p>
      </header>
      {response.status === "error" ? (
        <ResearchDataStatus subject="Sector directory" code={response.code} message={response.message} />
      ) : response.data.length === 0 ? (
        <ResearchDataStatus subject="Sector directory" code="empty" />
      ) : (
        <div className="mt-6 grid min-w-0 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {response.data.map((sector) => (
            <section key={sector.id}
              className="min-w-0 rounded-xl border border-slate-300 p-4 dark:border-slate-700 sm:p-5"
              aria-labelledby={`sector-${sector.id}`}>
              <h2 id={`sector-${sector.id}`} className="text-lg font-semibold">{sector.name}</h2>
              {sector.description && <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{sector.description}</p>}
              {sector.companies.length === 0 ? (
                <p className="mt-4 text-sm">No issuers currently listed for this sector.</p>
              ) : (
                <ul className="mt-4 space-y-2" aria-label={`Companies in ${sector.name}`}>
                  {sector.companies.slice(0, 5).map((company) => (
                    <li key={company.id}>
                      <Link
                        className="block min-h-11 rounded-md border border-slate-200 px-3 py-2 text-sm underline underline-offset-2 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 dark:border-slate-700 dark:hover:bg-slate-800"
                        href={`/companies/${company.id}`}>
                        <span className="font-medium">{company.name}</span>
                        <span className="ml-2 text-xs text-slate-600 dark:text-slate-300">({company.ticker})</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ))}
        </div>
      )}
    </main>
  );
}
