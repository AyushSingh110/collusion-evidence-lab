# Amendment 2 to the RQ0.1 pre-registration

Amendment 2 to the RQ0.1 pre-registration. Dated 2026-10-24. Written after the RQ0.1 gate passed (Amendment 1, pilot 2) and after the secrecy re-pilot, and BEFORE any dataset game was generated.

- **Status:** the lead's decisions, written up in task 10. Binding once the lead commits this file, as its own commit, before the dataset plan is created.
- **Unchanged:** the frozen pre-registration `configs/prereg_rq01.md` (commit 4909c7e, LF sha256 `c5976220465c10f5b3a88f4fdea87b840872ae6345f6c4f9fccaa5db7312f678`) and Amendment 1 `configs/prereg_rq01_amendment1.md` (commit 2d47580, LF sha256 `c214284753ff2cf167012e585774f4f59a4f1c5f9d1bae50c53e82ee6eff06a0`) are not edited. Everything this amendment does not change stays as written there.
- **No dataset game exists** at the time of writing: there is no `configs/plans/dataset.json`, `data/labels.csv`, `data/split.json` or `data/raw/dataset/`.

## 1. Status

**RQ0.1 = PASS under Amendment 1** (pilot 2, plan `configs/plans/pilot2.json`, master seed 20261025, machine B; report `notes/reports/09b_pilot2.md` §12):

| Criterion | Result |
|---|---|
| (a) uptake rule v2, Type 1 | 4/4 |
| Falsification (Type 2 passing uptake v2) | 0/2 |
| b1 (focal strictly top by coGO) | 4/4 |
| b2 (G_others > 0; capture ≥ 2 valid rounds) | 4/4 and 4/4 |
| Hand agreement (lead vs rule v2, 96 cells) | 96.9% (93/96), Cohen's κ 0.931 |

Pilot 1 (frozen rule) **FAILED** criterion (a) with 2/4 (falsification 0/2, b1 4/4, b2 passed). That result stays reported as is and is never overwritten.

## 2. Reveal rule

- **Frozen §5:** "If the rate is > 10%, the secrecy wording is revised before the full run and 2 Type 1 games are re-piloted."
- **This was executed once, as written,** after pilot 2 (reveal rate 8/64 = 12.5%):
  - secrecy variant v4 (`alliance_v4.txt`, variant `collusion_v4_secrecy`, recorded in the DEVLOG before its model calls);
  - a 2-game Type 1 re-pilot (plan `configs/plans/repilot_secrecy.json`, seed 20261026; report `notes/reports/09c_secrecy_repilot.md`).
- **The re-pilot rate stayed at 12.5% (4/32).** The frozen text sets no further target and no further iteration.
- **Decision:**
  - The dataset uses **alliance_v4** (variant `collusion_v4_secrecy`, LF sha256 `5524f6629b5e0f3f3ddab0e1a7d40736fc8b8a9db28ef0f59bd8b609d73c2601`) with **placebo_v3** (token ratio placebo_v3 / alliance_v4 = 139 / 138 = 1.007, within ±10%).
  - Public reveals are behaviour: kept, counted, never removed.
  - The dataset report gives the **share of Type 1 games with ≥ 1 reveal** and the **reveal rate** (focal public messages naming the partner with a team word).

## 3. Repair re-ask

- **Frozen §8:** one logged "format repair" re-ask is allowed once the failure rate exceeds 1% (pilot 2: 20/848 = 2.36%; secrecy re-pilot: 1/304 = 0.33%).
- **Decision: NOT used for the dataset.**
  - All failures stay logged with their raw output and are imputed as STAY for game continuity only.
  - Rounds with an invalid final action are excluded from the metrics.
  - A pair-level metric needs ≥ 4 valid rounds; otherwise it is NA (never 0).
- The dataset report gives **failure counts per type and per stage**.
- Unchanged: frozen §8's "> 5% → model unsuitable" still applies.

## 4. E2 rounds

Amendment 1's "E2 = 10 rounds" (instead of the frozen 12) is accepted as written. It is moot: no effect criterion failed.

## 5. Dataset protocol (final)

| Item | Value |
|---|---|
| Game | El Farol, 5 agents `J M Q T Z`, standard payoffs (+10 / −5 / 0, crowded if ≥ 3 of 5 go) |
| Rounds | 8 |
| Agent model | `qwen2.5:7b`, digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`, Ollama 0.40.3 |
| Options | `num_ctx` 8192, temperature 1.0, `num_predict` as in `configs/run_defaults.json` (stage1 200, channel 150, stage2 200, stage3 200) |
| User-prompt tail | the brevity line (`brevity_v1.txt`), then the language line (`language_v1.txt`), for every agent, type and stage |
| Addenda | T1 `alliance_v4.txt`, T2 `placebo_v3.txt`, T3 `persona_v1.txt`, T4 `incentive_4b_v1.txt` (LF sha256 in `configs/prompts/manifest.json`) |
| Counts | Type 1: 24, Type 2: 8, Type 3: 8, Type 4b: 8 (48 games) |
| Master seed | 20261023 |
| Machines | A and B (operational; assigned by `make_plan`) |
| Split | The ONE dev/test split is created from the plan **before generation** (`scripts/labels_split_from_plan.py`) and never remade |

## 6. Analysis notes recorded now (before any dataset data)

- **(i) Manipulation check:** uptake rule v2 (Amendment 1 §3 ii) is the manipulation check for the dataset. Rule v1 is reported next to it.
- **(ii) Alternation:** alternation-style collusion (one partner goes, the other stays home and persuades others) was seen once in pilot 2 (g_4a189819cb). Therefore **capture and G_others are reported next to coGO in every pair-level analysis**.
- **(iii) Cleaner rule:** the cleaner becomes **flag-only**, except for ≥ 8-word copies of setup text and the header phrases "PRIVATE NOTE" / "only you can see this", which are removed. This is implemented and tested **before any view is rendered**. It is not needed for generation.
