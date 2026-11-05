# P3 — research UI acceptance and scope

Issues #45–#52. This UI must fail closed when underlying sources or market quotes are missing.

## Company research views

- Issuer metadata is not a verified instrument identifier. Listings show the exact symbol, MIC, trading currency, instrument type and source-verification flag.
- Financial statements show provider, filing and retrieval date, reporting currency, unit, and report age. These describe **report freshness**, not real-time market freshness.
- Quotes show the observation date, quote currency, exchange MIC, provider link and retrieval date. No fabricated market price or EUR conversion is displayed.
- Missing, stale, unavailable, unsupported, invalid-provenance and non-computable records display a distinct accessible message. Error responses must never become 0.
- Financial charts are sourced only from complete, comparable annual statements with uniform reporting currency. Their exact numbers remain available in the accessible table.
- FCF = operating cash flow minus positive capex. Net debt = debt minus cash. P/E, EV, diluted per-share results and DCF remain unavailable unless their necessary verified inputs and assumptions exist.

## Review / regression procedure

1. Run `npm ci && npm run lint && npx tsc --noEmit && npm run build` in `apps/web`.
2. Inspect a valid issuer with no imported statements/quotes. Expect explicit empty-state messages and no zero-valued placeholders.
3. With the API unavailable, expect an error state for each section rather than a misleading 0 or empty chart.
4. Import source-verified annual reports with consistent currency to verify chart and table numbers, source links and currency unit labels match.
5. On a narrow viewport (320–390px), verify tables scroll horizontally and every section remains readable. On keyboard, Tab through the page and verify all links, buttons, summary disclosure and scrollable table regions.
6. Check an ADR and a local listing of the same issuer. Verify both exchange MIC and currency remain distinct; do not assume that every non-ADR is an ordinary local share.
7. Verify missing FX data prevents any EUR conversion; the UI must not silently assume FX parity.

No live data/provider contract is supplied by these changes; manual browser checks requiring imported issuer data remain outstanding.
