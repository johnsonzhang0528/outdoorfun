// Single-purpose URL helpers: trailing-slash normalization and query-string
// construction for internal (same-origin) links, plus a shared fallback
// origin constant. Not a canonical-tag or path-segment-encoding utility -
// see internalUrl()'s docstring for the exact contract.

// Astro.site is always set (astro.config.mjs declares `site`), so this
// fallback is normally dead code - but it must be a real, current origin
// rather than a stale/typo'd domain, since it is the value used if that
// invariant is ever broken by a future config change.
export const SITE_ORIGIN_FALLBACK = 'https://www.outdoorfun.com.tw';

/**
 * Builds a same-origin, root-relative internal URL with exactly one
 * trailing slash (the root path "/" is left as "/", never "//"), and a
 * correctly-encoded query string appended after that slash. A fragment
 * embedded in `path` (e.g. "/search#results") is preserved after the
 * slash+query and is never touched by the trailing-slash or query logic.
 *
 * Contract: pass RAW, unencoded values in both `path` and `query` - this
 * function owns all percent-encoding of query keys/values via
 * URLSearchParams. Do not call encodeURIComponent() before calling this,
 * or values will be double-encoded. This function does not encode `path`
 * segments themselves (e.g. spot/city names) - only trailing-slash
 * normalization and query construction are in scope here.
 *
 * A `query` value of `undefined` omits that key entirely (never becomes
 * the literal string "undefined").
 *
 * Only accepts root-relative internal paths (must start with exactly one
 * "/", never "//" or a scheme) - throws for anything that looks like an
 * external or protocol-relative URL, since this helper must never be used
 * to "normalize" one.
 */
export function internalUrl(path: string, query?: Record<string, string | undefined>): string {
  if (typeof path !== 'string' || !path.startsWith('/') || path.startsWith('//')) {
    throw new Error(`internalUrl() only accepts a root-relative internal path, got: ${JSON.stringify(path)}`);
  }

  const hashIndex = path.indexOf('#');
  const fragment = hashIndex === -1 ? '' : path.slice(hashIndex);
  let pathname = hashIndex === -1 ? path : path.slice(0, hashIndex);

  // Defensive: if a query string was embedded directly in `path` (callers
  // should prefer the `query` param instead), fold it in rather than
  // silently dropping it.
  const qIndex = pathname.indexOf('?');
  let existingQuery = '';
  if (qIndex !== -1) {
    existingQuery = pathname.slice(qIndex + 1);
    pathname = pathname.slice(0, qIndex);
  }

  // Exactly one trailing slash, except root stays "/".
  pathname = pathname === '/' ? '/' : pathname.replace(/\/+$/, '') + '/';
  // Collapse any accidental internal "//" beyond the single leading slash.
  pathname = '/' + pathname.slice(1).replace(/\/{2,}/g, '/');

  const params = new URLSearchParams(existingQuery);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined) continue;
      params.set(key, value);
    }
  }
  const queryString = params.toString();

  return pathname + (queryString ? `?${queryString}` : '') + fragment;
}
