"use client";

import { useState } from "react";

type Evidence = {
  metric_period: string;
  published_date: string;
  retrieved_at: string;
  source: string;
  source_url: string;
  reporting_currency: string;
  amount_unit: string;
};

type Insight = {
  status: "partial_verified";
  as_of: string;
  evidence: Evidence[];
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
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function generateInsight() {
    setLoading(true);
    setError(null);
    setInsight(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/ai/companies/${companyId}/generate-insight`, { method: "POST" });
      if (!response.ok) {
        if (response.status === 422) {
          setError("Not computable: current independently sourced financial statements are unavailable or have not passed verification.");
          return;
        }
        setError(`Unable to generate a research summary (HTTP ${response.status}).`);
        return;
      }
      const data = (await response.json()) as Insight;
      setInsight(data);
    } catch {
      setError("Research service unavailable. Try again after verifying the API connection.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded border p-4">
      <h2 className="text-xl font-semibold">Verified Financial Summary</h2>
      <p className="mt-2 text-sm text-gray-600">No AI investment score or price target is produced without verified valuation inputs.</p>
      <button className="mt-3 rounded bg-black px-3 py-2 text-white" onClick={generateInsight} disabled={loading}>
        {loading ? "Checking sources..." : "Generate sourced summary"}
      </button>
      {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
      {insight && (
        <div className="mt-4 space-y-3 text-sm">
          <p className="font-semibold">Status: {insight.status}; financial period: {insight.as_of}</p>
          <p>{insight.summary}</p>
          <p>{insight.quality_view}</p>
          <p>{insight.balance_sheet_view}</p>
          <p>{insight.valuation_view}</p>
          <h3 className="font-semibold">Evidence</h3>
          <ul className="list-disc pl-5">
            {insight.evidence.map((item) => (
              <li key={item.source_url + item.metric_period}>
                <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="underline">{item.source}</a>
                {" "}({item.metric_period}; retrieved {item.retrieved_at}; {item.reporting_currency} in {item.amount_unit})
              </li>
            ))}
          </ul>
          <p className="text-xs text-gray-600">{insight.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
