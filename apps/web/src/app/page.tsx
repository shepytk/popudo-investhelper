import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-3xl font-bold">Fundamental Investment Intelligence Platform</h1>
      <p className="mt-4 text-gray-700">
        MVP flow: Country → Sector → Company → Fundamentals → AI Insight.
      </p>
      <div className="mt-6 flex gap-4">
        <Link className="rounded bg-black px-4 py-2 text-white" href="/sectors">
          Browse Sectors
        </Link>
      </div>
    </main>
  );
}
