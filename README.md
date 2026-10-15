# TEM — EZ × Verizon invoice audit engine

Code only. Inputs, outputs and analysis reports are stored in Google Drive, folder **tem-claude**
(`tem-data-YYYYMMDD.zip`). Unzip that archive into the repo root to get the layout below, then run.

```
analysis/scripts/   document inventory, billing header extraction, Verizon CSV analysis (one-off scripts)
work/scripts/       invoice line parsers (VZ_INTL_*, US statements, other templates) and contract price extraction
work/engine/        discrepancy engine
  discrepancy.py      service x month ledger vs SOF/contract prices -> engine_out/service_month_ledger.csv
  rate_card.py        Amendment 28 (contract 208686) rate-card check  -> engine_out/rate_card_checks.csv
  us_stmt_rate_card.py  same check for US statements (circuit -> country/speed)
  fx_table.py         Currency Exchange Rate Table (stated rate > ECB rate on document date)
  findings.py         merges everything into tiers A-E    -> engine_out/findings.csv
```

Run (Python 3.12, stdlib only):

```
python3 -I work/engine/discrepancy.py && python3 -I work/engine/rate_card.py && python3 -I work/engine/findings.py
```

Some scripts under `analysis/scripts` and `work/scripts` still have hard-coded paths from the original workstation
(`/media/abhay/Workspace/Egon Zehnder/TEM`); the engine uses paths relative to the repo.
