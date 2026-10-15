# TEM rescue: Egon Zehnder (EZ) × Verizon

## Read this first
- **Presence360 (P360) is Staqo's own TEM product.** An outsourced third-party team started it about 1.5 years ago and botched it:
  - it can't reliably parse or extract EZ's Verizon documents
  - about 82% of its "overbilled" figure is false
  - its UI is poor
- **EZ (Egon Zehnder) is the anchor client.** They have stopped paying and will pull the plug **next week (week of 2026-10-19)** unless we overdeliver.
- This repo is the rescue. It holds a rebuilt audit engine, verified on EZ's real data, which will become the core of the rebuilt P360.
- **Scope:** Verizon only. Ignore NTT.

## The one deliverable: a sharp pack by Tuesday 2026-10-20
Everything goes into **one pack**, written to `deliverables/` (gitignored, mirrored to Drive `tem-claude`). It is not a demo and not a UI; product development continues after EZ is retained.

Write it for the decision chain:
- **Desh Deepak (procurement)** reads it first.
- **Manoj (finance)** has the final say.

Lead with what each of them can act on. Structure:
1. **One-page executive summary:** what P360 got wrong, what we found, what EZ should do now. Use plain numbers, each with a confidence level.
2. **Success-criteria scorecard.** Rows are the original promises in `Use Case Success Criteria.xlsx` (on Drive, in `TEM-dev-workspace`). Columns are what P360 delivered and what the new engine delivers, with evidence. The promises include:
   - detect ≥99% of discrepancies
   - reliable parsing
   - configurable rules
   - categorised exceptions
   - actionable reports
   - a 100% audit trail (file, field, rule, timestamp)
   - sign-off by 2 users
   - 6 months of history processed within 40 business days
   - a risk register
   - measurable outcomes

   Every criterion is a minimum, so beat it visibly.
3. **Claims, for Manoj.** Tier A and Tier B, each with the contract page and the invoice page as evidence. Each claim carries a **within-dispute-window flag** (see the risks below). Keep every finding, because expired claims are still leverage in the renewal.
4. **Spend baseline, for Manoj.** Monthly spend by service and country, reconciled to invoice header totals to the cent. Report monthly so it can be rolled up into either financial-year definition.
5. **Renewal facts, for Desh**, dug out of the contracts:
   - the term end date, auto-renewal and notice clause, and the dispute or billing-claim window. **Nobody at EZ knows these dates, so find them in the master agreement 208686, its amendments and the SOFs.**
   - billed rates vs Amendment 28
   - commitment and achievement-credit status: is the 12-month Interstate + International spend ≥ $2.0M, which earns a 4% credit (other tiers in the amendment)?
   - each service's term end and its early-termination exposure
   - the UAE 4 Mbps $5,280 anomaly
   - the Managed WAN and Internet Dedicated pricing gaps
6. **Verizon document-request list, for Desh, ready to send.** Nobody at EZ knows what to ask for. Start from §3.3.4 of the playbook, then add the gaps specific to EZ:
   - the Y2737467 US statements for 2023-05 → 2025-03
   - the signed K91936-00
   - the 15 missing contracts
   - the Managed WAN and Internet Dedicated rate exhibits
   - a full circuit inventory with term end dates
   - a commitment and achievement-credit statement
   - the dispute history
7. **Extraction coverage matrix.** For every Verizon document: header, lines, reconciliation, contract prices, and status OK / PARTIAL / FAILED. This is the proof that "we can read your documents now".
8. **Risks and open items,** each with a mitigation.

The financial year is unconfirmed: the user said "Nov–Sep". Ask whether that means Oct–Sep or Nov–Oct, and show both if there's no answer.

## Where things live
- **Code:** this repo, branch `ez-verizon-audit`. It holds code and docs only. **Never commit client data** (invoices, contract prices, findings, $ figures). `.gitignore` enforces this.
- **Data:** Google Drive `tem-claude/tem-data-20261015.zip` (also unzipped beside it). Unzip it into the repo root. It contains:
  - `analysis/` (incl. `FINDINGS.md`, `billing_index.csv`)
  - `work/` (`.txtcache` holds pdftotext output keyed by md5; `engine_out/`; `compare/legacy_vs_engine.html`)
  - `drive_new/`, `legacy/` and `teach/`
- **Original PDFs:** Drive `TEM-dev-workspace/Verizon/`, with subfolders `Invoice_Verizon`, `SOF_Verizon`, `Amendments_Verizon` (incl. `Executed Amendment 28.pdf`, 26 MB) and `Credit Notes_Verizon`. The same files are in the shared folder `TEM - Egon Zehnder` (`1g1OpxlJGbzKzTCraDPBKw2o_JU56Y3vo`). **Locally, download the Verizon folder from Drive and keep it outside the repo,** e.g. `~/tem-pdfs/Verizon`.
- **P360:** UAT https://tem-uat.thepresence360.com/, live https://tem.thepresence360.com/. **We don't have the P360 source code**, so the rebuild is effectively greenfield around this engine. `Presence 360 test case.csv` on Drive lists P360's current UI flows.
- **Industry research:** `docs/research/TEM_INDUSTRY_PLAYBOOK.md` covers:
  - standards and vocabulary, the billing-error taxonomy and the dispute lifecycle
  - competitor features (Tangoe, Calero, Sakon, Cass and others)
  - the renewal-pack contents and the carrier document-request list (§3.3.4)
  - UX and the screen inventory, the 2026 target architecture and data model
  - the rescue roadmap, P360's anti-patterns, and ready-to-use LLM prompts with JSON schemas (§6)

  Use it to set the pack's terminology and, later, the product rebuild.

## Run
Python 3.12, standard library only. You also need `poppler-utils` (pdftotext) and, optionally, `tesseract`.
```
python3 -I work/engine/discrepancy.py && python3 -I work/engine/rate_card.py && \
python3 -I work/engine/us_stmt_rate_card.py && python3 -I work/engine/findings.py
python3 -I work/compare/legacy_vs_engine.py      # head-to-head vs P360
```
**Tier A must stay at its audited value unless a change is explained.** Read `analysis/FINDINGS.md` first. Some `analysis/scripts` and `work/scripts` still have hard-coded paths from `/media/abhay/Workspace/Egon Zehnder/TEM`.

### Mistral OCR (Batch API, 50% cheaper)
`MISTRAL_API_KEY` must be set in the shell. The request format is **verified**: on 2026-10-15 a `probe` of a 64-page Verizon invoice succeeded with a base64 data URL and returned clean markdown.
```
python3 -I work/ocr/mistral_batch.py probe  <one.pdf>
python3 -I work/ocr/mistral_batch.py submit ~/tem-pdfs/Verizon     # --per-file 100
python3 -I work/ocr/mistral_batch.py status
python3 -I work/ocr/mistral_batch.py fetch                          # -> work/.ocrcache/<md5>.md|.json
```
**Priorities:**
1. The scanned SOFs and amendments (no text layer), above all **Amendment 28** and the master agreement. These hold the term, renewal, notice and dispute-window clauses, plus the rate card.
2. Invoices, as a second, independent read. Each invoice must reconcile to its header total, and every line where OCR and pdftotext disagree gets flagged.

## Engine state (2026-10-15)
- **Parsing.** Each Verizon layout has its own parser (international, US statements, India GST, Italy, credit notes). Each invoice must reconcile to its header to the cent. The attribution bug ("Product -" followed by a wrapped `(sid/contract)` token) is fixed in `work/scripts/vz_intl_lines.py`.
- **Contract resolution.** The engine uses the service and contract reference printed on each line, and never prices with a revision older than the cited one. If the contract is missing, the line goes to Tier E (unverifiable), not to discrepancy.
- **Pricing.**
  - SOFs: the monthly and one-time charge per service and site.
  - Amendment 28 rate card: keyed by product, speed, country and table (standard port vs DNM).
  - US statements: priced by the circuit's country, read from the `Orig:` line.
- **Comparison.** Per service per month, with proration by days. Credits are netted into their month, and one-time charges are compared cumulatively (Verizon bills some in instalments). Early-termination fees, pass-through costs and admin fees each go to their own bucket.
- **Tiers.**

  | Tier | Meaning | Value |
  |---|---|---|
  | A | Recoverable | $90,295 |
  | B | Claimable once confirmed (2 verified install overcharges + 1 pending a signed SOF) | $8,261 |
  | C | Early-termination fees | $62,911 |
  | D | Underbilled | $32,851 |
  | E | Unverifiable | ~$3.37M |
  | OK | Billed per contract | ~$3.25M |

  Claimable: **$95.6K** (+$3K pending).
- **Vs P360, on lines where a contract price was found.** P360 price-checks $0.75M of spend and flags $120.6K, of which only $21.9K (18%) is real. Our engine price-checks $3.57M and finds $95.6K of real errors.
- **Verification.** Precision on Tier A went from 2.5% to 27.5% to 80%, then every claim was verified row by row.
- **Gaps.** There's no UI or settlement tracking yet. About $3.37M stays unverifiable until the missing documents arrive.

## Risks
- **Dispute window.** The previous team never looked at it. Carrier agreements usually allow billing disputes for only 60–180 days. Find the clause, and flag each claim as within the window or expired.
- **Missing contracts:** ~$3.37M sits in Tier E. The request list (pack item 6) is how this gets fixed.
- **OCR misreads:** digits in OCR output are never trusted on their own. Every figure must cross-check against pdftotext or a header total.

## Working with this user
- Raise blockers directly, with the easy fix (settings, uploads, keys), instead of quietly working around them. Grill them when a decision is theirs to make.
- Use Sonnet and Haiku subagents for parallel work. You orchestrate them and check their numbers.
- **Verify every claim against the source text before reporting it.** Credibility is the whole game after 1.5 years of wrong numbers.
- Answers given so far: Desh then Manoj decide. EZ does not know the renewal date, so dig for it. The success-criteria file is the minimum to beat. Nobody knows what to request from Verizon.
