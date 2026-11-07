# AUTONOMY.md — running the factory without a human in the loop (except where the law says so)

*Process notes, 2026-11-06. Written after reviewing `prx0r/translation-work`
(`AGENTS.md`, `FINAL-PROCESS.md`, `check.py`, `tools/proof_record.py`,
`tools/readiness.py`, `tools/agent_contract.py`, `todoregistry.md`,
`mistakes.md`) and mapping what actually makes that stack runnable by an
unsupervised agent onto this repo's existing machinery.*

---

## 0. The autonomy ceiling — say it out loud

An autonomous factory does **not** mean "an agent does everything". It means:

> **The machine closes every loop that has a deterministic test, and stops
> exactly at the boundary of taste, rights, and money.**

Concretely, in bookfactory an agent may, without asking:

- read the queue and pick the next lane/action;
- place content from pinned upstream layers into entries;
- derive, build, render, package, verify, hash, re-render;
- fix anything a gate names, and re-run the gate;
- update `REGISTRY.json`, write proof records, append decisions;
- produce previews and one-link handoffs.

An agent may **never**:

- rule on structure law (sections, counts, inclusion/exclusion) — owner;
- mark a book shipped/published, upload to KDP, price it, or set rights;
- invent prose, a translation, a source, or a rights basis;
- overwrite a human signoff or an adjudication.

This is translation-work's "Machine proposes; humans dispose" with a
book-shaped edge: *the machine may also build and verify the physical object,
because the object has a deterministic gate.*

---

## 1. What we borrow from translation-work (and where it lands here)

| Pattern in translation-work | Why it works there | Landing point in bookfactory |
|---|---|---|
| One work at a time, end to end (`FINAL-PROCESS.md`) | Batches hide defects; a single lane keeps the gate's verdict meaningful | One lane at a time in the loop; parallel work only after a lane is `READY` |
| Data objects, not documents; Markdown is a view | Every claim is addressable and checkable | `thesis.json` / `book.json` / `entries.json` / `decisions.jsonl` — already the case |
| A single gate with exit codes (`check.py`: 0 = canonical) | An agent needs a binary verdict, not a paragraph | `check.py` already: exit 0 canonical, else names lane + stage + problem |
| Stage-aware gating (`DUE-LATER` vs `BLOCK`) | Lets a lane progress without pretending the future is done | Already implemented: `content → structure → formatting → build`, PDF last |
| `proof_record.py`: PASS/BLOCKED + `needs` + lineage | A blocked artifact says exactly what would unblock it | **To build**: per-book `proof/<book>.json` (see §6) |
| `readiness.py` burn-down matrix | Turns "where are we?" into one sortable screen | **To build**: `tools/readiness.py` (see §7) |
| `agent_contract.py describe/examples/validate` | An agent self-serves the exact shape + a legal example, no doc-diving | **To build**: `factory.py contract` (see §4) |
| `todoregistry.md` — one next action | Removes agent discretion about what to do next | **To build**: `NEXT.md` generated from readiness + registry |
| `human_authority/` + signoff files | Separates "verified" from "approved" | `decisions.jsonl` + `project.json.adjudications`; ship signoff still missing |
| `mistakes.md` — bars derived from real defects | Prevents relitigating the same bug | Adopt locally: `MISTAKES.md`, one entry per escaped defect |
| Immutable observations, decision log | Reconstructs why anything exists | `decisions.jsonl` already append-only + thesis-cited |

The big lesson: **autonomy is not a smarter model, it is a repo that can
answer three questions without a human:** *what is next*, *is it correct*,
*what exactly is missing*.

---

## 2. The state machine

```
            ┌──────────── pick one lane (queue order) ────────────┐
            ▼                                                     │
 content ──► structure ──► formatting ──► build ──► ship-ready ────┘
   │            │              │            │           │
   └─ entry     └─ thesis ↔    └─ fonts,    └─ audio    └─ owner signoff
      handoff      book agree     page count    plan +      + upload decision
      + rights      (gate)        (gate)        PDF proof     (never automatic)
```

Per lane, the machine only ever works on the **first stage that is not green**.
A lane that is green at `build` but lacks `ship-ready` is *not* an invitation to
polish; it is a stop sign that emits `needs: owner-signoff`.

`check.py <lane>` returns one of three shapes the loop must handle:

1. **BLOCK at stage S** → fix the named problem, rerun. Never advance.
2. **DUE-LATER** → not due; do not touch. Log it as the next stage's worklist.
3. **CANONICAL** → produce a proof record and consider a stage advance.

Stage advance is itself a gate: `factory.py stage --book B --to <stage>`
re-runs checks and refuses if the target stage is not actually green.

---

## 3. The queue: one next action, no discretion

The queue is a derived view, never hand-edited prose. Order:

1. any lane with a **BLOCK** at its current stage (oldest decision first);
2. any lane at `build` with all deterministic checks green but no
   `ship-ready` proof → emit `needs: owner-signoff` and **stop**;
3. the next lane in `REGISTRY.json.lanes` order that is not green;
4. nothing left → idle; do not invent work.

`NEXT.md` is generated (one screen, regenerated each loop) and contains:

```
NEXT: practical-prayers — build — 36 entries lack per-entry handoff (source/gate/rights/review)
WHY:  check.py BLOCK; needs per-entry source_path + text-gate PASS + rights + review record
DO:   place the 36 handoffs from translation-work (no retyping); re-run check.py
NOT:  no design changes, no audio render, no upload
```

The `NOT:` line matters as much as `DO:` — it is how a loop avoids drift.

---

## 4. The agent contract (self-serve context)

Translation-work's `agent_contract.py` exports, per layer: a structural
description, a *real* example with hashes, and a validate command. Port it:

```bash
python3 factory.py contract describe            # lanes, stages, gates, next action
python3 factory.py contract describe --stage build
python3 factory.py contract example --artifact entry   # one real, valid entries.json row
python3 factory.py contract example --artifact book
python3 factory.py contract validate --artifact entry --file /tmp/candidate.json
```

Rules:

- `example` returns a **real artifact from a green lane** plus its sha256 —
  never synthetic, never hand-picked stale data.
- `validate` runs the same schema + cross-checks as the gate. It never says
  "approved"; it says `valid` / `invalid: <path>: <message>`.
- An agent starts every unit of work by calling `describe`; it must not need
  to read `BOOKS.md` to act. Documentation is for humans and for *changes*.

---

## 5. The loop

One iteration = one bounded unit. Written so a harness (or a human) can run it
verbatim; every step is a command that exists or is listed in §13.

```text
loop until owner-stop or idle:

  1. next = factory.py next --json            # deterministic queue pick
     if next.kind == "idle": stop
     if next.kind == "owner":  notify + stop  # signoff / ruling / go

  2. ctx = factory.py contract describe --stage next.stage --json

  3. work = the smallest change that clears next.block
     - content: place blocks from pinned layers (extract, never write prose)
     - structure: change book.json/thesis.json only via factory.py decide
     - formatting: engine.py / css / counts
     - build: audio plan, PDF render, cover render, package
     (all renders >10s are detached jobs with their own log + notify)

  4. gate = check.py <lane>
     if BLOCK: fix what it names; goto 4         (max 3 attempts, then
                                                 write needs + stop)
     if DUE-LATER: ignore this iteration

  5. proof = factory.py proof --book <lane>      # deterministic, writes JSON
     if proof.gate == "BLOCKED": emit needs; stop

  6. independent critic (fresh agent, no shared context):
     - re-run the gate itself (never trusts step 4)
     - read the rendered artifact, not the source (PDF page, EPUB, cover)
     - name defects with the exact page/element
     Defects → back to 3. Clean → continue.

  7. factory.py registry --refresh               # stage, counts, proof state
     append decision(s) for every construction change (thesis-cited)

  8. if lane is green at build:
       factory.py proof --book <lane> --ship     # -> ship-ready, needs owner
       hand owner ONE link (outputs server), notify-send, stop
```

Hard loop rules:

- **No batch iterations.** One lane, one change, one gate per iteration.
- **Never fix a gate by weakening it.** Gate edits are owner decisions.
- **Never re-run a render to "see if it helps".** Re-run only after a named
  defect and a stated change; renders are logged jobs.
- **Stop on the third identical BLOCK.** That is a design problem, not a
  retry problem: write `needs` and surface it.
- **The critic is not the producer.** Different context, ideally a different
  agent; it must reproduce every PASS from the artifact itself.
- **Observation is immutable.** Proof records, manifests, and decisions are
  append-only. Corrections are new records.

---

## 6. Proof records (the envelope we take from `proof_record.py`)

Per book, one JSON, machine-generated, human-readable:

```json
{
  "book": "practical-prayers",
  "generated": "2026-11-06T21:20:00Z",
  "tool": "bookfactory proof v1",
  "lineage": {
    "thesis_sha256": "…", "book_json_sha256": "…", "entries_sha256": "…",
    "template_sha256": "…", "style_sha256": "…",
    "renderer_sha256": "…", "cover_style_sha256": "…",
    "source_files": [{"path": "…", "sha256": "…"}]
  },
  "checks": [
    {"id": "entry-provenance", "gate": "PASS", "detail": "36/36 source_path+ref resolve"},
    {"id": "text-gate",        "gate": "PASS", "detail": "36/36 GATE.json PASS"},
    {"id": "rights",           "gate": "BLOCKED", "detail": "GRETIL NC-SA unresolved (4 routes open)"},
    {"id": "interior",         "gate": "PASS", "detail": "108pp, 6x9, preflight PASS"},
    {"id": "cover",            "gate": "PASS", "detail": "318.01x234.95mm, spine 6.86mm"},
    {"id": "epub",             "gate": "PASS", "detail": "EPUB3 validated, 36 entries"},
    {"id": "package",          "gate": "PASS", "detail": "4 files, sha256 manifest"},
    {"id": "audio",            "gate": "PENDING", "detail": "0/72 clips — owner go + key"}
  ],
  "gate": "BLOCKED",
  "needs": ["rights: resolve GRETIL licence or record owner ruling",
            "audio: owner go + FISH key"],
  "note": "Machine-proposed. Not publication approval."
}
```

Why this and not just `check.py`'s exit code: the exit code says *whether*;
the record says *what the object is* and *what would unblock it*. It also
gives the owner a diffable artifact per build (hashes change only when the
thing changed), and it makes "did we ship the same book we verified?" a
one-line check.

`factory.py proof --book B` must be **read-only** apart from writing the
record; it may render a throwaway proof PDF only in a temp dir, never overwrite
shipped outputs.

---

## 7. Readiness matrix (one screen, sortable)

Columns per lane, à la `readiness.py`:

```
LANE                 STAGE       ENTRY  TEXT  RIGHTS  PDF   COVER  EPUB  AUDIO  PROOF  NEXT
practical-prayers    build       36/36  36/36  ?       108pp  ok     ok    0/72   BLOCK  rights+handoff
tantric-prayer       build       36/36  36/36  ?       108pp  ok     ok    0/72   BLOCK  rights+handoff
ipvv                 queued      —      —      —       —      —      —      —      —      proofs running
```

`factory.py status` prints this; `READY` requires: entry provenance all PASS,
text-gate all PASS, rights recorded, preflight PASS, cover+EPUB+package hashes
match, audio either `included` or explicitly `pending-owner`. Anything less
prints the one blocking need.

---

## 8. Needs taxonomy — what the machine can unblock itself

Every `needs` item is tagged so the loop never asks for the wrong thing:

| tag | meaning | self-unblockable? |
|---|---|---|
| `fix:<gate>` | the gate named a deterministic defect | yes — loop back to §5.3 |
| `source:<file>` | a layer file / ref is missing or unresolved | yes if the file exists upstream; else escalate |
| `rights:<item>` | licence/attribution question | **no** — owner ruling |
| `owner-go:<action>` | render spend, audio API spend, upload | **no** |
| `owner-taste:<artifact>` | design/typography choice | **no** |
| `owner-signoff:<book>` | shipping the verified object | **no** |

The loop's output must be honest about the category. "BLOCKED" without a
tagged need is a bug in the proof tool.

---

## 9. Roles and anti-self-approval

Three hats, at minimum two contexts:

1. **Producer** — makes the change, runs the fast gate.
2. **Critic** — fresh context; re-runs the deterministic gate *and* inspects
   the rendered artifact (PDF page, cover wrap, EPUB chapter) against the
   thesis/style/one-design law. Reports page-level defects.
3. **Registrar** — writes proof record + registry; never edits content.

The producer may not sign its own proof record. On this box that means: if
there is one model, run the critic as a separate session with only the
artifact + the contract, never with the producer's reasoning; if a second
box/agent is available, use it. This mirrors translation-work's rule that the
machine never marks a work COMPLETE — it marks it *machine-proposed, needs
human review* — extended with a second machine eye before the human one.

---

## 10. A day in the life (concrete)

```bash
# 00 — orientation, no doc-diving
python3 factory.py next --json
python3 factory.py contract describe --stage build --json
python3 factory.py status

# 01 — clear the named block (example: per-entry handoff)
#      place, never retype; one entry at a time; gate after each
python3 check.py practical-prayers
python3 factory.py proof --book practical-prayers

# 02 — build artifacts only when the gate is green to that stage
python3 prints/bookkit/engine.py prints/practical-prayers
python3 prints/bookkit/cover.py prints/practical-prayers
# blocks >10s: detached + log + notify, then return
python3 factory.py package --book practical-prayers
python3 check.py practical-prayers

# 03 — critic pass on the artifacts (fresh context), defects → 01

# 04 — record + hand over one link, then stop
python3 factory.py registry --refresh
runuser -u box -- env DISPLAY=:0 … notify-send "bookfactory" "practical-prayers: build green, needs owner signoff"
```

Every command above is either present today or specified in §13.

---

## 11. Failure log and bars

Create `MISTAKES.md` in this repo, append-only, one entry per escaped defect,
each turning into a check or a bar. Seed it with the ones already learned:

- a cover that passed `cover.pdf` existence but had stale interior proof
  (mixed generations) → M6 stale-output rule + proof-record hashes;
- EPUB failures from unescaped `<br>` in front matter → sanitize + validator
  (now a gate);
- raw dev filenames leaking into reader-facing footers → provenance is
  internal, never printed (new check: no source filename in rendered text);
- a build green at `formatting` treated as shippable → `ship-ready` proof is
  a separate state, never inferred from `CANONICAL`.

Rule of thumb from translation-work: **when the gate and the rule disagree,
the rule wins** — and the disagreement is a MISTAKES entry that strengthens
the gate.

---

## 12. Safety rails that autonomy must not erode

Inherited from this monorepo's standing rules (patala `AGENTS.md`):

- Renders/encodes never run on the hub — dispatch to the fleet; the hub ships
  bytes and shows results.
- Nothing blocks: any >10s operation is a detached job with its own log and
  `notify-send` on success *and* failure.
- One-link delivery: every artifact reaches the owner as a clickable outputs
  link, never a bare path.
- Dev-stage ceiling: no full render before the owner has seen EITHER a clip or
  (for books) the exact current proof; the machine may render one hard page,
  never a 43-page storyboard "to check".
- No deletions on this box without explicit owner instruction (disk rule).
- No upstream edits: translation-work is read-only input, pinned by hash.
- No network spend (TTS, uploads, cloud render) without `owner-go`.

---

## 13. Build order — the smallest additions that make §5 real

| # | Artifact | Acceptance test |
|---|---|---|
| 1 | `factory.py status` (readiness matrix) | prints every lane + one blocking need; deterministic ordering |
| 2 | `factory.py next` (queue) | returns exactly one of `{fix, build, owner, idle}` with lane/stage/reason |
| 3 | `factory.py contract` (describe/example/validate) | examples come from green lanes with sha256; validate runs schemas |
| 4 | `factory.py proof` (record + `--ship`) | writes `proof/<book>.json`; `--ship` refuses unless every non-owner check PASSes |
| 5 | `MISTAKES.md` + gate checks derived from it | each historical defect has a named check id in the proof record |
| 6 | `NEXT.md` generator | regenerated by `status`, never hand-edited, contains `DO:` and `NOT:` |
| 7 | `factory.py registry --refresh` | REGISTRY lanes/counts/stages match `check.py` reality |
| 8 | owner-signoff file (schema + writer) | `proof --ship` needs a signed record; unsigned = BLOCKED |

None of these changes the pipeline, the theses, or the design law. They make
the existing laws legible to a machine — which is the whole trick.

---

## 14. What never automates (write it on the wall)

1. **Structure law** — what the book *is* (sections, counts, inclusions).
2. **Taste** — design rulings, type, cover composition beyond the locked
   template.
3. **Rights** — licence readings and publication basis.
4. **Spend** — TTS/API/cloud/upload actions.
5. **Ship** — the decision to publish a verified object.
6. **Gate weakening** — changing what "correct" means.

Everything else — the entire gap between a decision and a verified artifact —
is the autonomous machine's job. If the loop ever finds itself waiting on a
human for something in that gap, that is a missing deterministic check, not a
reason for a human to be in the loop.

## Editorial copy (EXPLAINER.md)

Guide-field English (`brief`/`logic`/`howto`/`sign`) follows **`EXPLAINER.md`**.
Drafting a full 36-entry overlay is an **editorial proposal**: the producer may
build a candidate via `prints/practical-prayers/editorial/apply_preview.py`
(outside the repo) and **must stop for owner approval** before overwriting
`entries.json`. Source-QA BLOCKs are independent of copy approval.
