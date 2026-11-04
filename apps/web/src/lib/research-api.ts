export type FailureCode =
  | "missing_data" | "stale_data" | "company_not_found" | "not_computable"
  | "provider_unavailable" | "unsupported_industry" | "invalid_provenance"
  | "unavailable" | "request_failed";

export type ResearchResult<T> =
  | { status: "ok"; data: T }
  | { status: "error"; code: FailureCode; message: string; httpStatus?: number };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function researchGet<T>(path: string): Promise<ResearchResult<T>> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(12000),
    });
    if (response.ok) return { status: "ok", data: (await response.json()) as T };
    let detail: { code?: string; message?: string } | undefined;
    try {
      const payload = (await response.json()) as {
        detail?: string | { code?: string; message?: string };
      };
      if (typeof payload.detail === "object" && payload.detail !== null) detail = payload.detail;
    } catch {
      // Broken response bodies remain an explicit error.
    }
    const allowed: FailureCode[] = [
      "missing_data", "stale_data", "company_not_found", "not_computable",
      "provider_unavailable", "unsupported_industry", "invalid_provenance",
    ];
    const code = allowed.includes(detail?.code as FailureCode)
      ? (detail?.code as FailureCode) : "request_failed";
    return {
      status: "error", code, httpStatus: response.status,
      message: detail?.message || `Research service returned HTTP ${response.status}`,
    };
  } catch {
    return {
      status: "error", code: "unavailable",
      message: "The research service is unavailable. No financial values were substituted.",
    };
  }
}
