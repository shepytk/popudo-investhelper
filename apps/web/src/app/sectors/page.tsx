import Link from "next/link";

import { apiGet } from "@/lib/api";

type Company = { id: number; name: string; ticker: string };

type SectorWithCompanies = {
  id: number;
  name: string;
  description: string;
  companies: Company[];
};

export default async function SectorsPage() {
  const sectors = await apiGet<SectorWithCompanies[]>("/api/sectors/with-companies");

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-2xl font-semibold">Sectors</h1>
      <div className="mt-6 space-y-6">
        {sectors.map((sector) => (
          <section key={sector.id} className="rounded border p-4">
            <h2 className="text-xl font-medium">{sector.name}</h2>
            <p className="text-sm text-gray-600">{sector.description}</p>
            <ul className="mt-3 list-disc pl-6">
              {sector.companies.slice(0, 5).map((company) => (
                <li key={company.id}>
                  <Link className="text-blue-600 underline" href={`/companies/${company.id}`}>
                    {company.name} ({company.ticker})
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </main>
  );
}
