import { describe, expect, it } from "vitest";

import { buildOidcRedirectUri, parseOidcCallback } from "./auth";


describe("auth helpers", () => {
  it("builds a redirect URI from origin and pathname", () => {
    expect(
      buildOidcRedirectUri({
        origin: "https://paper.k-biofoundrycopilot.duckdns.org",
        pathname: "/workspace",
      }),
    ).toBe("https://paper.k-biofoundrycopilot.duckdns.org/workspace");
  });

  it("parses OIDC callback params from the location search string", () => {
    expect(parseOidcCallback("?code=abc&state=xyz&error_description=nope")).toEqual({
      code: "abc",
      state: "xyz",
      error: "",
      errorDescription: "nope",
    });
  });
});
