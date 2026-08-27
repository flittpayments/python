# Flitt Python SDK — Security Review

**Scope:** `flittpayments/python` SDK client only (gateway/backend behavior is out of scope).
**Reviewed:** `flittpayments/{api,helpers,utils,resources,checkout,payment,order,exceptions,configuration}.py`,
`setup.py`, `tests/*`, `README.md`. Includes the newly added `Payment.ibancredit()`,
`Checkout.open_banking()`, and `Checkout.installments()`.

**Note:** this document covers only the fixes applied in this PR. Additional lower-priority findings
surfaced during the review are being tracked and handled separately, outside this public document.

## Summary

| | Count |
|---|---|
| Fixed in this change | 7 |
| Verified passes (no finding) | 3 |

---

## Findings

### SEC-01 — No request timeout (availability / DoS)
- **Severity:** Medium | **Status:** Fixed in this PR
- **File:** `flittpayments/api.py` (`_request`)
- **Description:** `requests.request(method, url, data=data, headers=headers)` was called with no
  `timeout=`. A hung/black-holed remote connection could block the calling thread indefinitely — a
  real availability risk for a synchronous checkout/payment request handler.
- **Fix:** Added a `timeout` kwarg to `Api.__init__` (default `30` seconds), stored as `self.timeout`,
  passed into `requests.request(..., timeout=self.timeout)`.
- **Risk if unaddressed:** A slow/unresponsive gateway endpoint (network issue, DNS problem, or
  attacker-controlled `api_domain`) can wedge a merchant's request-handling worker forever.

### SEC-02 — XML entity-expansion DoS risk
- **Severity:** Medium | **Status:** Fixed in this PR
- **File:** `flittpayments/utils.py` (`from_xml`)
- **Description:** Used `xml.etree.cElementTree`, which does not resolve external entities (no
  classic file-read XXE) but does expand internal `<!DOCTYPE>`-defined entities by default
  (billion-laughs / quadratic-blowup). Reachable whenever `request_type='xml'` and the response body
  is attacker-influenced (compromised TLS/DNS, or a misconfigured `api_domain`).
- **Fix:** Swapped to `defusedxml.ElementTree`, added `defusedxml` to `setup.py` `install_requires`.
  Output is unchanged for any well-formed response without a DOCTYPE (i.e. everything the SDK
  currently receives from the real API).
- **Risk if unaddressed:** Defense-in-depth gap; not directly exploitable today without also
  compromising the response channel, but leaves no protection if that ever happens.

### SEC-03 — Unescaped XML serialization on outbound requests
- **Severity:** Low-Medium | **Status:** Fixed in this PR
- **File:** `flittpayments/utils.py` (`_data2xml`)
- **Description:** Leaf values and tag names were concatenated into XML with no `<`/`&`/`>` escaping.
  A field value (e.g. `order_desc`) containing those characters produced malformed or
  sibling-tag-injectable outbound XML.
- **Fix:** Wrapped leaf-value stringification and tag names with `xml.sax.saxutils.escape`. Verified:
  `to_xml({'order_desc': 'a<b&c'})` now produces `<order_desc>a&lt;b&amp;c</order_desc>` instead of
  malformed output; unchanged for values without special characters.
- **Risk if unaddressed:** Malformed/injectable outbound XML for any merchant-supplied free-text field.

### SEC-04 — Dead/broken list-serialization branch
- **Severity:** Low | **Status:** Fixed in this PR
- **File:** `flittpayments/utils.py` (`_data2xml`)
- **Description:** The list branch built `result_list` via recursive calls but returned
  `''.join(d)` (joining the original list, not the built strings) — always `TypeError`s on a list
  containing non-string items (e.g. `Order.settlement`'s `receiver` field, a list of dicts).
  Unreachable today because `settlement()` requires protocol `2.0`, which forces JSON — but worth
  fixing since new fields may introduce list values under XML in the future.
- **Fix:** `return ''.join(result_list)`.

### SEC-05 — Naive (`==`) signature comparison
- **Severity:** Low | **Status:** Fixed in this PR
- **File:** `flittpayments/helpers.py` (`is_valid`)
- **Description:** Inbound webhook/callback signature verification used plain string `==`, which
  short-circuits on the first differing byte — a timing side-channel an attacker could in principle
  use to probe a merchant's own webhook endpoint.
- **Fix:** `hmac.compare_digest(str(result_signature), str(signature))`. Verified functionally
  identical (correct signature → `True`, wrong signature → `False`) via direct test.

### SEC-06 — Card/IBAN data reachable via debug logs
- **Severity:** High (PCI-DSS relevant) | **Status:** Fixed in this PR
- **File:** `flittpayments/api.py` (`_request`, `_response`)
- **Description:** `log.debug('Data: %s' % str(data))` and `log.debug('Content: %s' % content)` logged
  the full serialized request/response body. For `Pcidss.step_one` this includes `card_number`/`cvv2`
  in plaintext; the new `Payment.ibancredit()` adds `receiver_iban`. A `logging.basicConfig(level=DEBUG)`
  anywhere downstream — common when chasing an unrelated bug — would write this to logs/log
  aggregators, a PCI-DSS violation for CVV specifically (CVV must never be stored, even transiently).
- **Fix:** Added `_mask_sensitive()`, a format-aware (json/xml/form) redaction helper applied only to
  the log calls (not the actual outbound/inbound payload) for `card_number`, `cvv2`, `receiver_iban`.
  Verified: masked output replaces all three fields with `***` while leaving other fields (e.g.
  `order_id`) intact.
- **Risk if unaddressed:** Silent PAN/CVV/IBAN exposure the moment DEBUG logging is enabled anywhere
  in a consuming application.

### SEC-07 — Unpinned HTTP client dependency
- **Severity:** Low-Medium | **Status:** Fixed in this PR
- **File:** `setup.py`
- **Description:** `requests`/`six` had no version floor at all. `requests` has had past releases
  fixing proxy/`Authorization`-header leakage on cross-scheme/cross-host redirects and related issues;
  an unpinned floor means a very old, unpatched version could silently be installed.
- **Fix:** Pinned `requests>=2.31.0`, `six>=1.12`, `defusedxml>=0.7.1`. **Note:** confirm the exact
  `requests` fixed-in version against the current CVE database before relying on `2.31.0` as gospel —
  it's a reasonable modern floor, not a number tied to one specific verified CVE ID in this review.
- **Risk if unaddressed:** No lower bound on a security-sensitive transitive dependency.

---

### Verified passes (recorded so they aren't re-litigated)

- **TLS certificate verification:** no `verify=False` anywhere in the codebase — `requests`' secure
  default is in effect.
- **Credentials never logged:** `secret_key` is never passed to `log.debug`/exceptions anywhere;
  only derived `signature` and non-secret data flow into logs (and, after SEC-06, sensitive payment
  fields are now also redacted from those logs).
- **Test fixture data (`tests/data/test_data.json`):** card numbers, `secret: "test"`, and small
  numeric merchant IDs are standard sandbox-only placeholder values (synthetic test-card BIN range,
  self-evidently non-production credentials) — not a leaked secret. The actual risk in this area is
  that the whole test suite runs live/uncredentialed against a sandbox with no HTTP mocking, which is
  a test-infra reliability concern, not a secrecy one — out of scope for this change.

---

## New Code Addendum — IBAN Withdrawal / Open Banking / Installments

Applied the same checklist to `Payment.ibancredit()`, `Checkout.open_banking()`, `Checkout.installments()`:

- **Logging:** `receiver_iban` is included in `_SENSITIVE_FIELDS` (SEC-06) and confirmed redacted from
  debug logs by direct test.
- **Required-field validation:** `ibancredit()` follows the same `helper.check_data(params)` pattern
  as every other resource method — `receiver_iban` is required and validated before any network call
  (confirmed: missing `receiver_iban` raises `RequestError` locally, no request sent).
- **`payment_method` validation:** `open_banking()`/`installments()` validate against the documented
  allowed bank list before delegating to `self.url()`, via the new `_validate_payment_method`
  staticmethod (mirrors `_validate_recurring_data`'s existing convention); confirmed raising
  `ValueError` for an invalid value.
- **No duplicated request-building/signing logic:** both new `Checkout` methods delegate to the
  existing `self.url()` — `_required()`, signing, and response parsing in `checkout.py`/`api.py` are
  unmodified.
- **Client-handling guidance documented, not enforced in the SDK:** the bank-app-deeplink handling
  rules (no auto-redirect, no iframe, no URL rewriting, confirm via server callback/status only) are
  client/mobile-app concerns outside this backend SDK's reach — captured prominently in both methods'
  docstrings and in the README so integrators don't misuse the returned `checkout_url`.
- **Negative-path tests added:** `test_open_banking_invalid_payment_method`,
  `test_installments_invalid_payment_method` in `tests/checkout_tests.py` — closing part of the test
  coverage gap noted below for the Checkout class generally.
- **IBAN format not client-side validated beyond non-empty:** `receiver_iban` is checked for presence
  only, not structural format (length/checksum). This matches the existing SDK convention (no other
  resource method does format validation beyond `_validate_recurring_data`'s date/period checks) and
  avoids duplicating validation the backend already performs (bank-routing decisions live server-side).
  Flagged here for visibility, not changed.

---

## Code Quality — "Redirect" (`Checkout`) class review

Requested as a best-practices/security/code-quality-only pass (no functional changes to
`url`/`token`/`verification`/`subscription`/`subscription_stop`/`_required`).

1. **Docstring/enforcement mismatch — fixed.** `subscription()`'s docstring documented `period` as
   `('day', 'month', 'year')` while `_validate_recurring_data` only accepts `('day', 'week', 'month')`
   — `'year'` always raised, `'week'` worked but wasn't documented. Docstring corrected to match
   actual enforcement.
2. **Partial validation coverage, reported only.** `subscription()`'s docstring documents
   `recurring_data.readonly`/`state` as constrained to `'y'`/`'n'`, but `_validate_recurring_data`
   only checks `start_time`/`period` format — `every`/`readonly`/`state` are never format-checked.
   Recommend either extending validation or further correcting the docstring; not changed here since
   extending validation could reject previously-accepted values.
3. **Inconsistent exception taxonomy, reported only.** `subscription()`/`subscription_stop()` raise a
   bare `Exception('This method allowed only for v2.0')` instead of one of the SDK's own typed
   exceptions (`RequestError`/`ValueError`, both used elsewhere in this same file). A caller catching
   `flittpayments.exceptions.RequestError` won't catch this. Recommend a dedicated exception type as a
   follow-up — this is a caught-exception-type change for existing integrations, so not bundled here.
4. **Dead code, reported only.** `Resource.get_url()` is defined but never called anywhere in the
   package or tests, despite being the natural accessor for `checkout_url`. Recommend wiring it into
   the README example or removing it.
5. **Mutable-default-argument footgun — fixed.** `Api.post(self, url, data=list, headers=None)`
   defaulted `data` to the `list` *type object*, not `[]`/`{}`. Harmless today (every caller passes
   `data=params` explicitly) but a latent footgun. Changed to `data=None` with `data = data or {}` at
   the top of the method body.
6. **Test coverage gap, partially addressed.** `tests/checkout_tests.py`'s original 8 tests were 100%
   happy-path against the live sandbox — none exercised `RequestError`/`ValueError`/the v2.0-only
   guard exceptions. The new `open_banking`/`installments` tests add 2 negative-path cases; recommend
   (follow-up, not part of this change) adding equivalent negative tests for the pre-existing
   `subscription()`/`url()` paths.
7. **Naming consistency — verified pass.** `order_id`/`order_desc`/`amount`/`currency` are used
   identically across `checkout.py`, `payment.py`, and `order.py`. No inconsistency found.

---

## Fixed in this PR

- [x] `api.py`: added `timeout=` (default 30s) to the `requests.request` call
- [x] `utils.py`: swapped to `defusedxml.ElementTree`; added `xml.sax.saxutils.escape` in `_data2xml`
- [x] `utils.py`: fixed dead/broken list-serialization branch in `_data2xml`
- [x] `helpers.py`: `hmac.compare_digest` in `is_valid`
- [x] `api.py`: redact `card_number`/`cvv2`/`receiver_iban` in debug logs via `_mask_sensitive`
- [x] `api.py`: fixed `Api.post`'s mutable/type-default `data=list` argument
- [x] `setup.py`: pinned `requests>=2.31.0`, `six>=1.12`; added `defusedxml>=0.7.1`
- [x] `checkout.py`: corrected `subscription()`'s `period` docstring to match actual enforcement
