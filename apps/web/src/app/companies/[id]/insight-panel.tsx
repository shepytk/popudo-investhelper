"use client";

import { useState } from "react";

type Insight = {
  summary: string;
  business_model: string;
  quality_view: string;
  growth_view: string;
  valuation_view: string;
  balance_sheet_view: string;
  risk_view: string;
  opportunities: string[];
  risks: string[];
  questions_for_further_research: string[];
  disclaimer: string;
};

export function InsightPanel({ companyId }: { companyId: number }) {
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);

  async function generateInsight() {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/ai/companies/${companyId}/generate-insight`, {
        method: "POST",
      });
      const data = (await response.json()) as Insight;
      setInsight(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded border p-4">
      <h2 className="text-xl font-semibold">AI Insight</h2>
      <button className="mt-3 rounded bg-black px-3 py-2 text-white" onClick={generateInsight} disabled={loading}>
        {loading ? "Generating..." : "Generate Insight"}
      </button>
      {insight && (
        <pre className="mt-4 overflow-x-auto rounded bg-gray-100 p-3 text-sm">{JSON.stringify(insight, null, 2)}</pre>
      )}
    </section>
  );
}
