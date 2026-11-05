"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function CompanyResearchError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log only the sanitized error class; avoid source responses or credentials.
    console.error("Company research rendering failed", error.name);
  }, [error]);

  return (
    <main className="mx-auto max-w-5xl space-y-4 px-4 py-6 sm:px-8 sm:py-10">
      <h1 className="text-xl font-semibold">Company research could not be displayed</h1>
      <p role="alert">The page encountered an unexpected error. Financial data has not been substituted with zeros.</p>
      <button type="button" onClick={reset}
        className="rounded border border-slate-500 px-4 py-2 focus-visible:outline-2 focus-visible:outline-offset-2">
        Retry loading research
      </button>
      <p><Link href="/sectors" className="underline underline-offset-2">Return to sectors</Link></p>
    </main>
  );
}
