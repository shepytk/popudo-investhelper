import Link from "next/link";

import { ValuationLab } from "@/components/valuation-lab";

export default function ValuationLabPage() {
  return (
    <main id="main-content" className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-8 sm:py-10">
      <nav aria-label="Research navigation">
        <Link href="/" className="underline underline-offset-2 focus-visible:outline-2">Home</Link>
      </nav>
      <header>
        <h1 className="text-3xl font-semibold">Valuation methodology</h1>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          A self-contained hypothetical model. No real issuer is valued until its financial data, assumptions
          and security identity are independently verified.
        </p>
      </header>
      <ValuationLab />
    </main>
  );
}
