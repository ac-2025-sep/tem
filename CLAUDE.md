# TEM — Egon Zehnder (EZ) × Verizon invoice audit

Staqo is replacing EZ's current TEM platform (Presence360). EZ is very unhappy with it because it can't reliably parse or extract their Verizon documents. EZ's financial year is being confirmed: the user said "Nov–Sep", so ask whether that means Oct–Sep or Nov–Oct. **The Verizon contract renewal is due next month.** Scope is Verizon only. Ignore NTT.

## Where things live
- **Code:** this repo, branch `ez-verizon-audit`. Code only. Never commit client data (invoices, contract prices, findings, reports with $ figures). `.gitignore` enforces this.
- **Data and reports:** Google Drive folder **tem-claude**, `tem-data-YYYYMMDD.zip`. Unzip it into the repo root. It contains `analysis/`, `work/` (parsed data, `.txtcache`, `engine_out/`), `drive_new/`, `legacy/` and `teach/`. If it isn't in the session yet, ask the user to upload it.
- **Original PDFs:** Drive project folder `1g1OpxlJGbzKzTCraDPBKw2o_JU56Y3vo` (Verizon, Data Dump). The user exported these as `drive-download-20261014T073330Z-1-001*.zip`. Ask the user to upload them when raw PDFs are needed. Pulling more than about 30 PDFs one at a time through the Drive connector is too slow.

## Run
```
python3 -I work/engine/discrepancy.py && python3 -I work/engine/rate_card.py && \
python3 -I work/engine/us_stmt_rate_card.py && python3 -I work/engine/findings.py
python3 -I work/compare/legacy_vs_engine.py      # head-to-head vs Presence360
```
Tier A must stay at its audited value unless a change is explained. Read `analysis/FINDINGS.md` in the data zip first.

## State at hand-off (2026-10-15)
- The engine is verified through two audits plus a row-by-row review of Tier B. Findings are tiered A–E, and claims cite the contract page and the invoice page.
- The comparison with the legacy platform is done: `work/compare/legacy_vs_engine.html` in the data zip.
- The parser attribution bug ("Product -" followed by a wrapped `(sid/contract)` token) is fixed in `work/scripts/vz_intl_lines.py`.

## Next steps (agreed with the user)
1. **Mistral OCR via the Batch API** (`work/ocr/mistral_batch.py`). `MISTRAL_API_KEY` is an environment secret. Run `probe` on one PDF first to confirm that base64 data URLs are accepted, then `submit` the PDF directory, then `status` and `fetch`. Output goes to `work/.ocrcache/<md5>.md`, keyed like `.txtcache`. Treat OCR and pdftotext as two independent reads: every invoice must reconcile to its header total, and every line where they disagree gets flagged. OCR is mainly needed for the scanned SOFs and amendments (no text layer).
2. **Extraction coverage matrix** for every Verizon document: header, lines, reconciliation, contract prices, and status OK / PARTIAL / FAILED. This is the core pitch against Presence360.
3. **Renewal pack** for next month's negotiation:
   - spend run-rate by service and country (monthly series, so it can be rolled up by financial year)
   - billed rates vs Amendment 28
   - commitment end dates and early-termination exposure
   - the claims to offset, plus the UAE 4 Mbps $5,280 anomaly
   - achievement-credit tiers (12-month Interstate + International ≥ $2.0M → 4% …) and whether EZ qualifies
   - Managed WAN and Internet Dedicated pricing gaps
   - missing documents
4. **Documents still needed from EZ or Verizon:** the Y2737467 US statements for 2023-05 → 2025-03, the signed K91936-00, 15 missing contracts, and the Managed WAN and Internet Dedicated rate exhibits.

## Working with this user
- Tell them about blockers directly, with the easy fix (settings, uploads, keys), instead of quietly working around them.
- Use Sonnet and Haiku subagents for parallel work. You orchestrate and check their numbers.
- Verify every claim against the source text before reporting it.
