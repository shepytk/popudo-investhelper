import { apiGet } from "@/lib/api";

import { InsightPanel } from "./insight-panel";

type Company = {
  id: number;
  name: string;
  ticker: string;
  exchange: string;
  description: string;
  country_id: number;
  sector_id: number;
};

type Financial = {
  fiscal_year: number;
  revenue: number;
  net_income: number;
  free_cash_flow: number;
  total_debt: number;
};

export default async function CompanyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const companyId = Number(id);
  const company = await apiGet<Company>(`/api/companies/${companyId}`);
  const financials = await apiGet<Financial[]>(`/api/companies/${companyId}/financials`);

  return (
    <main className="mx-auto max-w-4xl p-8 space-y-6">
      <section className="rounded border p-4">
        <h1 className="text-2xl font-semibold">
          {company.name} ({company.ticker})
        </h1>
        <p className="text-sm text-gray-600">{company.exchange}</p>
        <p className="mt-3">{company.description}</p>
      </section>

      <section className="rounded border p-4">
        <h2 className="text-xl font-semibold">Fundamentals</h2>
        <table className="mt-3 w-full table-auto text-left text-sm">
          <thead>
            <tr>
              <th>Fiscal Year</th>
              <th>Revenue</th>
              <th>Net Income</th>
              <th>Free Cash Flow</th>
              <th>Total Debt</th>
            </tr>
          </thead>
          <tbody>
            {financials.map((item) => (
              <tr key={item.fiscal_year}>
                <td>{item.fiscal_year}</td>
                <td>{item.revenue}</td>
                <td>{item.net_income}</td>
                <td>{item.free_cash_flow}</td>
                <td>{item.total_debt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <InsightPanel companyId={company.id} />
    </main>
  );
}
