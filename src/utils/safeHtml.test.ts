// Run with: node --experimental-strip-types --test src/utils/safeHtml.test.ts
// Uses Node's built-in test runner (Node 18+) so no new dependency is needed.
import assert from 'node:assert/strict';
import test from 'node:test';
import {
  escapeHtml,
  isAllowedExternalUrl,
  isSafeInternalPath,
  toSafeJsonScript,
} from './safeHtml.ts';

test('escapeHtml neutralizes HTML-special characters', () => {
  assert.equal(escapeHtml('<img src=x onerror=alert(1)>'), '&lt;img src=x onerror=alert(1)&gt;');
  assert.equal(escapeHtml(String.fromCharCode(34) + String.fromCharCode(39) + '&<>'), '&quot;&#39;&amp;&lt;&gt;');
  assert.equal(escapeHtml(null), '');
  assert.equal(escapeHtml(undefined), '');
  assert.equal(escapeHtml('plain text'), 'plain text');
});

test('toSafeJsonScript round-trips to the same value via JSON.parse', () => {
  const cases: unknown[] = [
    { a: 1, b: 'hello' },
    ['x', 'y', 'z'],
    { desc: 'line1\nline2', quote: String.fromCharCode(34) + 'quoted' + String.fromCharCode(34) },
    { unicode: String.fromCharCode(0x2028) + String.fromCharCode(0x2029) },
    null,
    42,
    'a plain string',
  ];
  for (const value of cases) {
    const serialized = toSafeJsonScript(value);
    assert.deepEqual(JSON.parse(serialized), value);
  }
});

test('toSafeJsonScript defeats every </script> variant', () => {
  const payloads = [
    '</script>',
    '</ScRiPt>',
    '</SCRIPT >',
    '<script>alert(1)</script>',
    'a & b < c > d',
  ];
  for (const payload of payloads) {
    const serialized = toSafeJsonScript({ value: payload });
    assert.equal(serialized.toLowerCase().includes('</script'), false, 'leaked for payload index ' + payloads.indexOf(payload));
    assert.deepEqual(JSON.parse(serialized), { value: payload });
  }
});

test('toSafeJsonScript escapes U+2028 / U+2029', () => {
  const ls = String.fromCharCode(0x2028);
  const ps = String.fromCharCode(0x2029);
  const serialized = toSafeJsonScript({ value: 'a' + ls + 'b' + ps + 'c' });
  assert.equal(serialized.includes(ls), false);
  assert.equal(serialized.includes(ps), false);
  assert.equal(serialized.includes('\\u2028'), true);
  assert.equal(serialized.includes('\\u2029'), true);
  assert.deepEqual(JSON.parse(serialized), { value: 'a' + ls + 'b' + ps + 'c' });
});

const ALLOWED = ['allowed.example', 'www.outdoorcampingworld.com'];

test('isAllowedExternalUrl accepts exact-match https hosts', () => {
  assert.equal(isAllowedExternalUrl('https://allowed.example/path', ALLOWED), true);
  assert.equal(isAllowedExternalUrl('https://www.outdoorcampingworld.com/x', ALLOWED), true);
});

test('isAllowedExternalUrl rejects scheme tricks', () => {
  assert.equal(isAllowedExternalUrl('javascript:alert(1)', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('JaVaScRiPt:alert(1)', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('data:text/html,<script>alert(1)</script>', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('vbscript:msgbox(1)', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('//evil.example', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('http://allowed.example', ALLOWED), false); // http, not https
});

test('isAllowedExternalUrl rejects hostname bypass attempts', () => {
  assert.equal(isAllowedExternalUrl('https://allowed.example.evil.test', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('https://evil-allowed.example', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('https://allowed.example@evil.test/', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('https://user:pass@allowed.example/', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('https://allowed.example.', ALLOWED), false); // trailing dot
});

test('isAllowedExternalUrl is case-insensitive on hostname, but rejects non-standard ports', () => {
  assert.equal(isAllowedExternalUrl('https://ALLOWED.EXAMPLE/path', ALLOWED), true);
  assert.equal(isAllowedExternalUrl('https://allowed.example:443/path', ALLOWED), true); // default port, same resource
  assert.equal(isAllowedExternalUrl('https://allowed.example:8443/path', ALLOWED), false);
  assert.equal(isAllowedExternalUrl('https://allowed.example:80/path', ALLOWED), false);
});

test('isAllowedExternalUrl rejects malformed / non-string / empty input', () => {
  assert.equal(isAllowedExternalUrl('', ALLOWED), false);
  assert.equal(isAllowedExternalUrl(undefined, ALLOWED), false);
  assert.equal(isAllowedExternalUrl(null, ALLOWED), false);
  assert.equal(isAllowedExternalUrl(123, ALLOWED), false);
  assert.equal(isAllowedExternalUrl('not a url at all', ALLOWED), false);
  assert.equal(isAllowedExternalUrl({}, ALLOWED), false);
});

test('isSafeInternalPath accepts root-relative paths only', () => {
  assert.equal(isSafeInternalPath('/images/camps/default.webp'), true);
  assert.equal(isSafeInternalPath('/images/featured/glamping.jpg'), true);
});

test('isSafeInternalPath rejects protocol-relative and unsafe paths', () => {
  assert.equal(isSafeInternalPath('//evil.example/x.jpg'), false);
  assert.equal(isSafeInternalPath('https://evil.example/x.jpg'), false);
  assert.equal(isSafeInternalPath('images/x.jpg'), false); // not root-relative
  assert.equal(isSafeInternalPath('/x' + String.fromCharCode(34) + 'onerror=alert(1)'), false);
  assert.equal(isSafeInternalPath('/x' + String.fromCharCode(39) + 'onerror=alert(1)'), false);
  assert.equal(isSafeInternalPath('/x<script>'), false);
  assert.equal(isSafeInternalPath('/x' + String.fromCharCode(0) + 'y'), false); // NUL byte
  assert.equal(isSafeInternalPath('/x/valid-path.jpg'), true); // sanity: safe paths still pass
  assert.equal(isSafeInternalPath(''), false);
  assert.equal(isSafeInternalPath(undefined), false);
});
