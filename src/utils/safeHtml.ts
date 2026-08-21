// Shared, minimal sanitization helpers. Each function targets exactly one
// trust context - do not blend them, since HTML-escaping, JSON-for-script
// embedding, and URL validation each guard against a different attack shape.

const HTML_ESCAPE_MAP: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

/** Escapes a value for safe insertion into HTML text or an attribute value. */
export function escapeHtml(value: unknown): string {
  const str = value === null || value === undefined ? '' : String(value);
  return str.replace(/[&<>"']/g, (ch) => HTML_ESCAPE_MAP[ch]);
}

// Built from numeric char codes (not literal characters) so this source file
// contains no invisible/ambiguous Unicode code points.
const LINE_SEPARATOR = new RegExp(String.fromCharCode(0x2028), 'g');
const PARAGRAPH_SEPARATOR = new RegExp(String.fromCharCode(0x2029), 'g');

/**
 * Serializes a value for embedding inside an HTML <script> element (e.g.
 * `set:html={toSafeJsonScript(data)}`). Escaping every `<`/`>`/`&` means no
 * literal `</script` sequence (in any case) can ever survive in the output,
 * and U+2028/U+2029 are escaped too since they are otherwise valid inside a
 * JSON string but can terminate a JS statement in some embedding contexts.
 * The result still round-trips through JSON.parse() to the original value.
 */
export function toSafeJsonScript(value: unknown): string {
  return JSON.stringify(value)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(LINE_SEPARATOR, '\\u2028')
    .replace(PARAGRAPH_SEPARATOR, '\\u2029');
}

function parseUrlStrict(value: unknown): URL | null {
  if (typeof value !== 'string' || value.trim() === '') return null;
  try {
    // No base argument: protocol-relative ("//evil.example") and other
    // relative forms fail to parse rather than silently resolving.
    return new URL(value);
  } catch {
    return null;
  }
}

/**
 * True only if `value` is an https:// URL whose hostname exactly matches one
 * of `allowedHosts` (case-insensitive, no suffix/prefix/substring matching),
 * with no embedded userinfo (user:pass@host). Use a distinct `allowedHosts`
 * list per trust context (e.g. affiliate links vs. ad images) - do not share
 * one list across unrelated purposes.
 */
export function isAllowedExternalUrl(value: unknown, allowedHosts: readonly string[]): boolean {
  const url = parseUrlStrict(value);
  if (!url) return false;
  if (url.protocol !== 'https:') return false;
  if (url.username || url.password) return false;
  const hostname = url.hostname.toLowerCase();
  return allowedHosts.some((h) => h.toLowerCase() === hostname);
}

/**
 * True only if `value` is a same-origin, root-relative path ("/images/x.jpg").
 * Rejects protocol-relative URLs ("//host/x"), and any character that could
 * break out of an HTML attribute or be misused for control-character tricks.
 * This is intentionally separate from isAllowedExternalUrl: an internal path
 * and an external affiliate URL are different trust models and must not
 * share a validation function.
 */
export function isSafeInternalPath(value: unknown): boolean {
  if (typeof value !== 'string' || value === '') return false;
  if (!value.startsWith('/') || value.startsWith('//')) return false;
  for (let i = 0; i < value.length; i++) {
    const code = value.charCodeAt(i);
    if (code < 0x20) return false; // control characters
  }
  if (/["'<>\\]/.test(value)) return false;
  return true;
}
