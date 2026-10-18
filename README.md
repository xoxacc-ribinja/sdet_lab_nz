# SDET Lab NZ

A small, gradually growing system-test automation lab. Development starts on macOS; Linux/Windows environments can be added when a real test scenario requires them.

## Layout

- `sut/` — programs we test from the outside, initially `sample_app.py`.
- `automation/` — automation code written during learning sessions.
- `tests/` — automated checks, added when needed.
- `reports/daily/`, `reports/weekly/`, `reports/monthly/` — free-form NZ learning reports (no fixed templates).
- `tools/save_report.py` — local macOS clipboard-to-Git report saver.
- `STATE.md` — short handoff for the next chat or model.

## First SUT

Run these on macOS from the repository root:

```sh
python3 sut/sample_app.py ok
python3 sut/sample_app.py fail
python3 sut/sample_app.py slow
```

`ok`: stdout `RESULT: OK`, exit 0. `fail`: stderr `ERROR: simulated failure`, exit 17. `slow`: stdout `STARTED`, waits about 5 seconds, then stdout `RESULT: OK`, exit 0. Missing or unknown mode exits 2.

The SUT is provided; the learner's work is to build automation around it, with new mechanisms explained before they're required. Real employer code and secrets must never be committed.

## Context recovery

Read `STATE.md`, then the latest reports and relevant code before resuming. The historical repository `xoxacc-ribinja/nz_sdet` is for historical evidence only, not current lesson contracts or administrative rules. Keep reports useful and natural rather than filling out predetermined forms.
