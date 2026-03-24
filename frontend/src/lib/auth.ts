export function buildOidcRedirectUri({
  origin = typeof window !== "undefined" ? window.location.origin : "",
  pathname = typeof window !== "undefined" ? window.location.pathname : "/"
} = {}): string {
  const cleanPath = `/${String(pathname || "/").trim().replace(/^\/+/, "").replace(/[#?].*$/, "")}`;
  if (origin && origin !== "null") {
    return `${origin}${cleanPath === "//" ? "/" : cleanPath}`;
  }
  return cleanPath === "//" ? "/" : cleanPath;
}

export function parseOidcCallback(search = typeof window !== "undefined" ? window.location.search : "") {
  const params = new URLSearchParams(String(search || "").replace(/^\?/, ""));
  return {
    code: String(params.get("code") || "").trim(),
    state: String(params.get("state") || "").trim(),
    error: String(params.get("error") || "").trim(),
    errorDescription: String(params.get("error_description") || "").trim()
  };
}

export function stripOidcCallbackParams(url = typeof window !== "undefined" ? window.location.href : "") {
  const parsed = new URL(String(url), "http://localhost");
  parsed.searchParams.delete("code");
  parsed.searchParams.delete("state");
  parsed.searchParams.delete("error");
  parsed.searchParams.delete("error_description");
  return `${parsed.pathname}${parsed.search}${parsed.hash}`;
}

export function buildOidcAuthorizationUrl({
  authorizationEndpoint,
  clientId,
  redirectUri,
  scopes = "openid profile email",
  state
}: {
  authorizationEndpoint: string;
  clientId: string;
  redirectUri: string;
  scopes?: string;
  state: string;
}): string {
  const url = new URL(authorizationEndpoint);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("scope", scopes);
  url.searchParams.set("state", state);
  return url.toString();
}
