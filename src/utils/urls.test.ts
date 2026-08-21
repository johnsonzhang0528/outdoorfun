// Run with: node --experimental-strip-types --test src/utils/urls.test.ts
import assert from 'node:assert/strict';
import test from 'node:test';
import { internalUrl, SITE_ORIGIN_FALLBACK } from './urls.ts';

test('SITE_ORIGIN_FALLBACK is the real, current site origin', () => {
  assert.equal(SITE_ORIGIN_FALLBACK, 'https://www.outdoorfun.com.tw');
});

test('internalUrl preserves the root path as exactly "/"', () => {
  assert.equal(internalUrl('/'), '/');
});

test('internalUrl adds exactly one trailing slash, no query', () => {
  assert.equal(internalUrl('/search'), '/search/');
  assert.equal(internalUrl('/topic/best-winter'), '/topic/best-winter/');
});

test('internalUrl does not duplicate an existing trailing slash', () => {
  assert.equal(internalUrl('/search/'), '/search/');
  assert.equal(internalUrl('/search//'), '/search/');
  assert.equal(internalUrl('/search///'), '/search/');
});

test('internalUrl collapses accidental internal double slashes', () => {
  assert.equal(internalUrl('/city//台南市'), '/city/台南市/');
});

test('internalUrl with a single query param', () => {
  assert.equal(internalUrl('/search', { q: 'beginner' }), '/search/?q=beginner');
});

test('internalUrl encodes Chinese characters and spaces in query values', () => {
  const result = internalUrl('/search', { q: '左跑浪' });
  assert.equal(result, '/search/?q=%E5%B7%A6%E8%B7%91%E6%B5%AA');
  // decoded value round-trips to the original semantic meaning
  const decoded = new URLSearchParams(result.split('?')[1]).get('q');
  assert.equal(decoded, '左跑浪');

  const withSpace = internalUrl('/search', { q: '新港 (大溪漁港)' });
  const decodedSpace = new URLSearchParams(withSpace.split('?')[1]).get('q');
  assert.equal(decodedSpace, '新港 (大溪漁港)');
});

test('internalUrl correctly encodes &, =, +, % in query values', () => {
  const cases = ['a&b', 'a=b', 'a+b', 'a%b', 'a&b=c+d%e'];
  for (const value of cases) {
    const result = internalUrl('/search', { q: value });
    const decoded = new URLSearchParams(result.split('?')[1]).get('q');
    assert.equal(decoded, value, `round-trip failed for: ${value}`);
  }
});

test('internalUrl omits a query key whose value is undefined (never the string "undefined")', () => {
  const result = internalUrl('/search', { q: undefined });
  assert.equal(result, '/search/');
  assert.equal(result.includes('undefined'), false);
});

test('internalUrl omits missing/empty query object entirely', () => {
  assert.equal(internalUrl('/search', {}), '/search/');
  assert.equal(internalUrl('/search', undefined), '/search/');
});

test('internalUrl does not double-encode a value that already looks percent-encoded', () => {
  // Contract: callers pass raw values. A raw value that happens to contain a
  // literal "%" character (not an intentional escape sequence) must still
  // round-trip correctly - this is the "avoid double encoding" requirement
  // interpreted as: encode exactly once, from the raw input, every time.
  const raw = '100% wave';
  const result = internalUrl('/search', { q: raw });
  const decoded = new URLSearchParams(result.split('?')[1]).get('q');
  assert.equal(decoded, raw);
});

test('internalUrl preserves a fragment after the trailing slash and query', () => {
  assert.equal(internalUrl('/search#results'), '/search/#results');
  assert.equal(internalUrl('/search#results', { q: 'x' }), '/search/?q=x#results');
});

test('internalUrl rejects protocol-relative and external URLs', () => {
  assert.throws(() => internalUrl('//evil.example'));
  assert.throws(() => internalUrl('https://www.outdoorfun.com.tw/search'));
  assert.throws(() => internalUrl('http://evil.example'));
  assert.throws(() => internalUrl('javascript:alert(1)'));
});

test('internalUrl throws for non-string or non-root-relative input', () => {
  assert.throws(() => internalUrl(''));
  assert.throws(() => internalUrl('search')); // missing leading slash
  // @ts-expect-error deliberately wrong type for a runtime guard test
  assert.throws(() => internalUrl(undefined));
});

test('internalUrl real call-site equivalents used across this PR', () => {
  assert.equal(internalUrl('/search'), '/search/');
  assert.equal(internalUrl('/search', { q: '左跑浪' }), '/search/?q=%E5%B7%A6%E8%B7%91%E6%B5%AA');
  assert.equal(internalUrl(`/city/${'台南市'}`), '/city/台南市/');
  assert.equal(internalUrl(`/spot/${'上三灣'}`), '/spot/上三灣/');
  assert.equal(internalUrl(`/topic/${'all-advanced'}`), '/topic/all-advanced/');
});
