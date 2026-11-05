# P3 #50 — Hypothetical valuation methodology and charts

The `/valuation-lab` screen is a **standalone, manually populated scenario calculator**. It is not a valuation of any real issuer. The calculation engine has no market-data, database, storage, API, UI, or network dependency, and the UI does **not** pull missing financial values from company profiles.

## SOLID module boundaries

- `src/lib/valuation/model.ts` — single responsibility: immutable domain input/result types and pure discounted-cash-flow valuation. No side effects.
- `src/lib/valuation/input.ts` — single responsibility: validate and convert explicit form text into typed domain parameters. Empty values never become zeros.
- `src/lib/valuation/scenarios.ts` — scenario construction, sensitivity evaluation and margin-of-safety calculation; reuses the same DCF function for all variants.
- `src/components/valuation-lab.tsx` — UI state, labels, accessible visualizations and a tabular alternative only. No business-logic formulas embedded in the component.
- `src/app/valuation-lab/page.tsx` — routing and description only.

A future adapter can inject verified issuer facts into the same `ValuationInputs` contract. Do not couple valuation logic directly to a data provider or React state.

## Financial methodology

For each of N years, FCF(t) = FCF(0) × (1 + g)^t.

PV(FCF(t)) = FCF(t) / (1 + r)^t.

Terminal value at year N = FCF(N) × (1 + g_terminal) / (r − g_terminal), requiring r > g_terminal.

Enterprise value = sum PV(FCF(t)) + PV(terminal value).

Equity value = enterprise value − net debt.

Intrinsic value per diluted share = equity value / diluted shares outstanding.

Margin of safety = (intrinsic value − user-supplied price) / intrinsic value, only if intrinsic value > 0 and the comparison price is valid.

All monetary enterprise/equity/FCF inputs use **millions of one selected currency**, and the share denominator uses **millions of diluted shares**. Per-share values therefore use that same currency. No implied currency conversion occurs.

Bear and bull change the FCF growth rate by the entered number of percentage points. The sensitivity table varies terminal growth and discount rate and explicitly marks mathematically invalid combinations N/A. The forecast plot and table use identical pure-domain projections.

## Acceptance and boundaries

- Start with blank monetary assumptions. No fabricated defaults, implied issuer quotes, preloaded forecasts or derived scores.
- An unsupported/missing/invalid assumption produces a visible error, not a fake zero valuation.
- Zero net debt is a valid **explicit** value.
- Test deterministic zero-growth perpetuity: FCF=100m, r=10%, g=0%, no net debt, 100m diluted shares gives intrinsic value of 10 per share.
- Test r <= terminal growth refuses to compute.
- A full revenue/earnings/FCF chart already uses source-backed annual financials on company pages. This standalone lab adds hypothetical projected FCF, bear/base/bull values and DCF discount/terminal-growth sensitivity with accessible tables.
- Future real-issuer valuations remain subject to independent source, securities, share-count and assumption verification and must not claim to have been produced by the scenario lab.
- Automated frontend build, structural tests and Chromium + axe-core browser acceptance run in CI.
