# Provider licence and data-use gate (P2-04)

**Scope:** User research platform, internal dev and future commercial availability. This register is a **review checklist**, not a grant of redistribution rights.

| Source | Current integration | Permitted product use | Storage / caching | Redistribution / public display | AI or derived outputs | Status |
| --- | --- | --- | --- | --- | --- | --- |
| SEC EDGAR companyfacts and submissions | Adapter and manual verified CIK linking | Public government filing data; technical access requires provider-specific fair-use compliance | Keep immutable retrieval evidence and documented attribution | Confirm SEC site terms and any third-party filing content rights for the intended display | Validate attribution, provenance, fair-use limits and third-party content | **Research-only until reviewed** |
| ECB Euro foreign exchange reference rates | XML importer | Official EUR reference rates; informational, not executable prices | Dated records with source URL and snapshot hash | Confirm ECB reuse and attribution conditions before external display | Derived FX conversions must retain source/date | **Research-only until reviewed** |
| OpenFIGI | Planned only; no API key configured | Developer account/API key subject to provider's terms | Review caching and quotas before enabling | Mapping metadata may have provider-specific restrictions | Verify any permitted downstream mappings before public use | **Not integrated / blocked** |
| European equity fundamentals / security identifiers | Not selected | No supplier agreement | No raw data ingestion until terms established | No public display or resale until licensed | No model-training/redistribution assumptions | **Unlicensed / blocked** |
| Exchange EOD quotes and corporate actions | Not selected | No supplier agreement | No import until reviewed | Venue entitlements vary by market and use | No display or derived use without authorization | **Unlicensed / blocked** |

## Launch control

The system must **not** expose third-party licensed content through public endpoints or UI until the designated operator documents the precise provider contract, account tier, territories, instruments, attribution, permitted cache retention, redistribution, AI use, and any venue-specific entitlements.

- API reads currently expose only the existing source-backed dataset; they do **not** implement provider-license-aware per-user entitlements.
- No data-provider key belongs in a Next.js `NEXT_PUBLIC_` variable.
- Add explicit machine-enforced allowlists/entitlements to data-serving routes before turning on commercial or publicly accessible hosting.
- Revisit provider terms at onboarding and when data licences or tiers change. Keep documentation of the reviewed version and decision date.
- SEC and ECB have different terms and rate limits; they are not interchangeable with commercial financial-data providers.

**P2 #38 remains open** until a real provider/usage decision and automated redistribution constraints are in place.

## Machine-enforced redistribution protection

In production the API now denies sourced statement, fact, quote, exchange-listing and ECB FX records unless **all underlying providers** are included in `INVESTHELPER_PUBLIC_DATA_PROVIDERS`. The default is empty (deny all). A malformed list or wildcard also fails closed. No provider is approved automatically merely because a filing or quote is publicly accessible. Development and test environments are not subject to this production redistribution gate.

The licensing policy module lives at `services/api/app/licensing.py`. An operator may add a provider **only after** recording the applicable agreement, account tier, geography, user type, storage limit, redistribution rights and AI permissions in this inventory. For example, configuring `sec_edgar` is a deliberate operational approval, not evidence that use is legally permitted.

Generated AI insights currently lack a complete machine-readable lineage of every input source and therefore remain disabled for public production delivery until that source-to-insight provenance is added. Basic issuer directory labels and any future endpoints also require independent source classification before release.

**#38 remains open** until contracts are approved, endpoint coverage is audited, provider-aware rights are enforceable per user/account where required, and a production acceptance test verifies actual configuration.
