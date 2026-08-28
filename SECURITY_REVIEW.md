# Flitt Python SDK — Security Review

**Scope:** `flittpayments/python` SDK client only (gateway/backend behavior is out of scope).
**Reviewed:** `flittpayments/{api,helpers,utils,resources,checkout,payment,order,exceptions,configuration}.py`,
`setup.py`, `tests/*`, `README.md`. Includes `Payment.ibancredit()`, `Checkout.open_banking()`, and
`Checkout.installments()`.

## Summary

| | Count |
|---|---|
| Fixed in this change | 4 |
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

### SEC-02 — Naive (`==`) signature comparison
- **Severity:** Low | **Status:** Fixed in this PR
- **File:** `flittpayments/helpers.py` (`is_valid`)
- **Description:** Inbound webhook/callback signature verification used plain string `==`, which
  short-circuits on the first differing byte — a timing side-channel an attacker could in principle
  use to probe a merchant's own webhook endpoint.
- **Fix:** `hmac.compare_digest(str(result_signature), str(signature))`. Verified functionally
  identical (correct signature → `True`, wrong signature → `False`) via direct test.

### SEC-03 — Card/IBAN data reachable via debug logs
- **Severity:** High (PCI-DSS relevant) | **Status:** Fixed in this PR
- **File:** `flittpayments/api.py` (`_request`, `_response`)
- **Description:** `log.debug('Data: %s' % str(data))` and `log.debug('Content: %s' % content)` logged
  the full serialized request/response body. For `Pcidss.step_one` this includes `card_number`/`cvv2`
  in plaintext; `Payment.ibancredit()` adds `receiver_iban`. A `logging.basicConfig(level=DEBUG)`
  anywhere downstream — common when chasing an unrelated bug — would write this to logs/log
  aggregators, a PCI-DSS violation for CVV specifically (CVV must never be stored, even transiently).
- **Fix:** Added `_mask_sensitive()`, a format-aware (json/form) redaction helper applied only to
  the log calls (not the actual outbound/inbound payload) for `card_number`, `cvv2`, `receiver_iban`.
  Verified: masked output replaces all three fields with `***` while leaving other fields (e.g.
  `order_id`) intact.
- **Risk if unaddressed:** Silent PAN/CVV/IBAN exposure the moment DEBUG logging is enabled anywhere
  in a consuming application.

### SEC-04 — Unpinned HTTP client dependency
- **Severity:** Low-Medium | **Status:** Fixed in this PR
- **File:** `setup.py`
- **Description:** `requests`/`six` had no version floor at all. `requests` has had past releases
  fixing proxy/`Authorization`-header leakage on cross-scheme/cross-host redirects and related issues;
  an unpinned floor means a very old, unpatched version could silently be installed.
- **Fix:** Pinned `requests>=2.31.0`, `six>=1.12`. **Note:** confirm the exact
  `requests` fixed-in version against the current CVE database before relying on `2.31.0` as gospel —
  it's a reasonable modern floor, not a number tied to one specific verified CVE ID in this review.
- **Risk if unaddressed:** No lower bound on a security-sensitive transitive dependency.

---

### Verified passes (recorded so they aren't re-litigated)

- **TLS certificate verification:** no `verify=False` anywhere in the codebase — `requests`' secure
  default is in effect.
- **Credentials never logged:** `secret_key` is never passed to `log.debug`/exceptions anywhere;
  only derived `signature` and non-secret data flow into logs (and, after SEC-03, sensitive payment
  fields are now also redacted from those logs).
- **Test fixture data (`tests/data/test_data.json`):** card numbers, `secret: "test"`, and small
  numeric merchant IDs are standard sandbox-only placeholder values (synthetic test-card BIN range,
  self-evidently non-production credentials) — not a leaked secret. The actual risk in this area is
  that the whole test suite runs live/uncredentialed against a sandbox with no HTTP mocking, which is
  a test-infra reliability concern, not a secrecy one — out of scope for this change.

---

## New Code Addendum — IBAN Withdrawal / Open Banking / Installments

Applied the same checklist to `Payment.ibancredit()`, `Checkout.open_banking()`, `Checkout.installments()`:

- **Logging:** `receiver_iban` is included in `_SENSITIVE_FIELDS` (SEC-03) and confirmed redacted from
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
  `test_installments_invalid_payment_method` in `tests/checkout_tests.py`.

---

## Code Quality — "Redirect" (`Checkout`) class review

Requested as a best-practices/security/code-quality-only pass (no functional changes to
`url`/`token`/`verification`/`subscription`/`subscription_stop`/`_required`).

1. **Docstring/enforcement mismatch — fixed.** `subscription()`'s docstring documented `period` as
   `('day', 'month', 'year')` while `_validate_recurring_data` only accepts `('day', 'week', 'month')`
   — `'year'` always raised, `'week'` worked but wasn't documented. Docstring corrected to match
   actual enforcement.
2. **Mutable-default-argument footgun — fixed.** `Api.post(self, url, data=list, headers=None)`
   defaulted `data` to the `list` *type object*, not `[]`/`{}`. Harmless today (every caller passes
   `data=params` explicitly) but a latent footgun. Changed to `data=None` with `data = data or {}` at
   the top of the method body.
3. **Naming consistency — verified pass.** `order_id`/`order_desc`/`amount`/`currency` are used
   identically across `checkout.py`, `payment.py`, and `order.py`. No inconsistency found.

---

## Fixed in this PR

- [x] `api.py`: added `timeout=` (default 30s) to the `requests.request` call
- [x] `helpers.py`: `hmac.compare_digest` in `is_valid`
- [x] `api.py`: redact `card_number`/`cvv2`/`receiver_iban` in debug logs via `_mask_sensitive`
- [x] `api.py`: fixed `Api.post`'s mutable/type-default `data=list` argument
- [x] `setup.py`: pinned `requests>=2.31.0`, `six>=1.12`
- [x] `checkout.py`: corrected `subscription()`'s `period` docstring to match actual enforcement
