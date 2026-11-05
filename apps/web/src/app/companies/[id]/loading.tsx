/** Suspense fallback while an issuer's source-backed research is fetched. */
export default function LoadingCompanyResearch() {
  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-8 sm:py-10" aria-busy="true">
      <div role="status" aria-live="polite" className="rounded-lg border border-slate-300 p-5 dark:border-slate-700">
        <h1 className="text-xl font-semibold">Loading company research</h1>
        <p className="mt-2 text-sm">Checking issuer details, financial statements, exchange listings and source-verified quotes.</p>
        <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">Missing records will be identified explicitly. No prices or financial values are estimated during loading.</p>
      </div>
    </main>
  );
}
