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


## November 2026 remaining P3 implementation

- Screener: `/screener` supports sourced company metadata search, country/sector ID filters, bounded pagination and responsive, keyboard-readable tables. No synthetic scores or financial rankings.
- Calculations: company pages display source-attributed FCF and net-debt arithmetic where comparable verified statement inputs exist. P/E, EV, dilution and DCF definitions are visible, and values stay unavailable when essential source inputs or assumptions are absent.
- EUR comparisons: `GET /api/fx/eur-reference?currency=USD&as_of=YYYY-MM-DD` retrieves a dated, source-hashed ECB fixing. The company quote display divides the verified listing's native quote by the relevant 1-EUR fixing only for a same-day or up-to-five-day-old rate, clearly marking the result indicative (not tradable). No FX source means no converted amount.
- Visuals: annual revenue, earnings and FCF charts use the same annual report values shown in the accessible table; they never mix currencies or replace missing values with zero.
- Accessibility: semantic main, navigation, table headings, keyboard-focusable horizontal table regions, labeled controls, touch targets and descriptive chart text. Automated static and build checks are CI-enforced; real-browser screen reader tests should still be run before a public release.

### Data-dependent limitations

Live provider account selection, authoritative complete listing/ISIN coverage, multi-year sourced valuation assumptions, shares outstanding and full dilution adjustments are unfinished P1/feature-platform work. In their absence the UI must explicitly display not computable; do not close a data-ingestion issue based only on UI implementation.

### Useful checks

```sh
python scripts/check_p3_research_ui.py
PYTHONPATH=services/api:. INVESTHELPER_ENV=test INVESTHELPER_DATABASE_URL=sqlite:///./p3-test.db python -m pytest -q services/api/tests/test_p3_fx_reference.py
cd apps/web && npm ci && npm run lint && npx tsc --noEmit && npm run build
```
