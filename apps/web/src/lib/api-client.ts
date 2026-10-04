import { ApiErrorResponse } from "@/types";

export class ApiError extends Error {
  code: string;
  statusCode: number;
  details: Record<string, unknown>;
  requestId: string;

  constructor(
    message: string,
    code: string = "INTERNAL_ERROR",
    statusCode: number = 500,
    details: Record<string, unknown> = {},
    requestId: string = ""
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.requestId = requestId;
  }
}

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
  params?: Record<string, string | number | boolean | undefined>;
}

const DEFAULT_TIMEOUT_MS = 30000;
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("insightflow_auth_token");
  } catch {
    return null;
  }
}

export async function apiRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, params, headers, ...restOptions } = options;

  let url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined) searchParams.append(key, String(val));
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const token = getAuthToken();
  const isFormData = restOptions.body instanceof FormData;

  const requestHeaders: Record<string, string> = {
    Accept: "application/json",
    "X-Client-Timestamp": new Date().toISOString(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(headers as Record<string, string>),
  };

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const isJson = response.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await response.json() : null;

    if (!response.ok) {
      const errorData = data as ApiErrorResponse | null;
      if (errorData?.error) {
        throw new ApiError(
          errorData.error.message,
          errorData.error.code,
          response.status,
          errorData.error.details,
          errorData.error.request_id
        );
      }
      throw new ApiError(
        `Request failed with status ${response.status}`,
        "HTTP_ERROR",
        response.status
      );
    }

    return data as T;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) {
      throw error;
    }
    if ((error as Error).name === "AbortError") {
      throw new ApiError("Request timed out", "REQUEST_TIMEOUT", 408);
    }
    throw new ApiError(
      (error as Error).message || "Network error occurred",
      "NETWORK_ERROR",
      0
    );
  }
}

export async function apiDownload(endpoint: string, filename: string): Promise<void> {
  const token = getAuthToken();
  const url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    throw new ApiError(`Download failed with status ${response.status}`, "DOWNLOAD_ERROR", response.status);
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export const api = {
  get: <T>(url: string, options?: RequestOptions) => apiRequest<T>(url, { ...options, method: "GET" }),
  post: <T>(url: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(url, { ...options, method: "POST", body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined }),
  upload: <T>(url: string, formData: FormData, options?: RequestOptions) =>
    apiRequest<T>(url, { ...options, method: "POST", body: formData }),
  put: <T>(url: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(url, { ...options, method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(url: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(url, { ...options, method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(url: string, options?: RequestOptions) => apiRequest<T>(url, { ...options, method: "DELETE" }),
  download: apiDownload,
};
