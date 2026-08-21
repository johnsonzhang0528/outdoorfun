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

test('internalUrl keeps an empty-string query value instead of omitting it', () => {
  const result = internalUrl('/search', { q: '' });
  assert.equal(result, '/search/?q=');
  const params = new URLSearchParams(result.split('?')[1]);
  assert.equal(params.has('q'), true);
  assert.equal(params.get('q'), '');
});

test('internalUrl keeps a numeric 0 query value instead of treating it as falsy', () => {
  const result = internalUrl('/search', { page: 0 });
  assert.equal(result, '/search/?page=0');
  assert.equal(new URLSearchParams(result.split('?')[1]).get('page'), '0');
});

test('internalUrl accepts non-zero numeric query values too', () => {
  const result = internalUrl('/search', { page: 3 });
  assert.equal(result, '/search/?page=3');
});

test('internalUrl only omits undefined, never empty string or 0, when mixed in the same call', () => {
  const result = internalUrl('/search', { q: '', page: 0, sort: undefined });
  const params = new URLSearchParams(result.split('?')[1]);
  assert.equal(params.has('sort'), false);
  assert.equal(params.get('q'), '');
  assert.equal(params.get('page'), '0');
});

test('internalUrl adds the trailing slash correctly when path already has an embedded query', () => {
  assert.equal(internalUrl('/search?q=beginner'), '/search/?q=beginner');
  // slash comes before the query, not after or interleaved
  const result = internalUrl('/search?q=beginner');
  assert.equal(result.indexOf('/?'), 7); // ".../search" + "/?..." — slash immediately precedes "?"
  assert.equal(result, '/search/?q=beginner');
});

test('internalUrl folds an embedded query in path together with the query param object', () => {
  const result = internalUrl('/search?city=hualien', { q: 'beginner' });
  const params = new URLSearchParams(result.split('?')[1]);
  assert.equal(params.get('city'), 'hualien');
  assert.equal(params.get('q'), 'beginner');
  assert.equal(result.startsWith('/search/?'), true);
});

test('internalUrl does not double-encode a query value that is already percent-encoded in the input path', () => {
  // Distinct from the raw-"%"-character test above: here the *input itself*
  // is a pre-encoded query string embedded in `path` (the defensive fold-in
  // case, not the "pass raw values to `query`" contract). URLSearchParams
  // decodes it once on parse and re-encodes it once on output, so the
  // result must contain exactly one layer of percent-encoding - never
  // "%25E5..." (which would mean the literal "%" from the input got
  // re-encoded on top of the existing encoding).
  const preEncoded = '/search?q=%E5%B7%A6%E8%B7%91%E6%B5%AA';
  const result = internalUrl(preEncoded);
  assert.equal(result, '/search/?q=%E5%B7%A6%E8%B7%91%E6%B5%AA');
  assert.equal(result.includes('%25'), false); // no double-encoding artifact
  const decoded = new URLSearchParams(result.split('?')[1]).get('q');
  assert.equal(decoded, '左跑浪'); // decodes back to the original semantic value
});

test('internalUrl never produces a stray "/?" when there is no query to append', () => {
  for (const result of [
    internalUrl('/'),
    internalUrl('/search'),
    internalUrl('/search', {}),
    internalUrl('/search', { q: undefined }),
  ]) {
    assert.equal(result.includes('?'), false, `unexpected "?" in: ${result}`);
  }
  assert.equal(internalUrl('/'), '/');
  assert.equal(internalUrl('/search'), '/search/');
  assert.equal(internalUrl('/search', {}), '/search/');
  assert.equal(internalUrl('/search', { q: undefined }), '/search/');
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
