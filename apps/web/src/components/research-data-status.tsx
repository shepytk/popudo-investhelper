import Link from "next/link";

import type { FailureCode } from "@/lib/research-api";

type DataStatusProps = {
  subject: string;
  code: FailureCode | "empty";
  message?: string;
};

const descriptions: Record<FailureCode | "empty", string> = {
  missing_data: "No independently sourced records have been imported for this item.",
  stale_data: "Only stale observations are available. They cannot be treated as current market data.",
  company_not_found: "This issuer was not found in the available company directory.",
  not_computable: "Required verified financial inputs are missing; a calculation cannot be shown.",
  provider_unavailable: "The upstream data provider could not be reached. No substitute financial values were generated.",
  unsupported_industry: "This data or calculation is not supported for this industry.",
  invalid_provenance: "The source or validation checks failed. Unverified observations are withheld.",
  unavailable: "The research API is unreachable. No financial values were substituted.",
  request_failed: "The research API returned an error. No financial values were substituted.",
  empty: "There are no verified records to display yet.",
};

export function ResearchDataStatus({ subject, code, message }: DataStatusProps) {
  return (
    <div role={code === "empty" || code === "missing_data" ? "status" : "alert"}
      className="mt-3 rounded-lg border border-slate-300 bg-slate-50 p-4 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
      <p className="font-semibold">{subject}: {code.replaceAll("_", " ")}</p>
      <p className="mt-1">{descriptions[code]}</p>
      {message && <p className="mt-1 text-slate-700 dark:text-slate-300">{message}</p>}
      <p className="mt-2 text-xs">
        <Link href="/sectors" className="underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2">
          Browse other sectors
        </Link>
      </p>
    </div>
  );
}
