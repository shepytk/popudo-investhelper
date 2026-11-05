import Link from "next/link";

export default function Home() {
  return (
    <main id="main-content" className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-8 sm:py-12">
      <h1 className="text-3xl font-bold">Popudo investment research</h1>
      <p className="max-w-2xl text-slate-700 dark:text-slate-300">
        Browse companies and review financial statements backed by sources. Missing valuation data is displayed as unavailable, not estimated.
      </p>
      <nav aria-label="Research navigation" className="grid gap-4 sm:grid-cols-2">
        <Link href="/screener" className="flex min-h-14 items-center rounded-lg border border-slate-500 p-4 font-medium underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2">Search and filter companies</Link>
        <Link href="/sectors" className="flex min-h-14 items-center rounded-lg border border-slate-500 p-4 font-medium underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2">Browse sectors</Link>
      </nav>
    </main>
  );
}
