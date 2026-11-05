import { researchGet } from "@/lib/research-api";

type FxReference = {
  base_currency: string;
  quote_currency: string;
  eur_to_quote: string;
  observed_date: string;
  source_url: string;
  source_sha256: string;
  provider: string;
  as_of: string;
};

type DatedQuote = { close: string; currency_code: string; date: string };

export async function EurQuote({ quote }: { quote: DatedQuote }) {
  if (quote.currency_code === "EUR") {
    return <p className="text-xs">EUR quote: no currency conversion necessary.</p>;
  }
  const response = await researchGet<FxReference>(
    "/api/fx/eur-reference?currency=" + encodeURIComponent(quote.currency_code) +
    "&as_of=" + encodeURIComponent(quote.date),
  );
  if (response.status === "error") {
    return <p className="text-xs" role="status">Indicative EUR conversion unavailable: no matching sourced ECB fixing.</p>;
  }
  const fx = response.data;
  const age = (Date.parse(quote.date + "T00:00:00Z") - Date.parse(fx.observed_date + "T00:00:00Z")) / 86400000;
  const rate = Number(fx.eur_to_quote);
  const amount = Number(quote.close);
  if (fx.base_currency !== "EUR" || fx.quote_currency !== quote.currency_code || fx.as_of !== quote.date ||
      fx.provider !== "ecb_fx" || !fx.source_url.startsWith("https://") ||
      !/^[0-9a-f]{64}$/i.test(fx.source_sha256) ||
      !Number.isInteger(age) || age < 0 || age > 5 ||
      !Number.isFinite(rate) || rate <= 0 || !Number.isFinite(amount) || amount < 0) {
    return <p className="text-xs" role="status">Indicative EUR conversion unavailable: invalid or stale source evidence.</p>;
  }
  const converted = (amount / rate).toLocaleString("en", { maximumFractionDigits: 2 });
  return (
    <p className="text-xs">
      Approx. {converted} EUR at <a href={fx.source_url} target="_blank" rel="noopener noreferrer" className="underline">
        ECB reference rate</a> on {fx.observed_date} (1 EUR = {fx.eur_to_quote} {fx.quote_currency}).
      Reference rate only; not an executable trade price. Values are rounded for display.
    </p>
  );
}
