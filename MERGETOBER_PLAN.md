# Mergetober 2026: execution plan

Written 2026-10-26 (about 11:30 IST) by the planning session.
**Executor:** a Claude Code session at medium effort. **Human:** Vividh (@VividhDesign).
Executor: read the whole file before acting, then start at Phase 0. Do not skip the gates.

---

## 0. Summary

**Goal.** Get **one** eligible, high-quality data-source connector PR opened in
`topoteretes/cognee-community` by Oct 31 and merged afterwards. One merged PR is a full entry in
the 20 × $100 draw (people are drawn, not PRs). Go for a second PR only if a second assignment
arrives early enough to build it to the same standard.

**Top Contributor is not a goal.** The current leaders have about 1 merged connector each, plus
1–3 more already deep in review. Nothing new has merged since Oct 21. One reviewer has done the
connector reviews, at 2–3 rounds per PR. Starting from zero with no assignment, we can't catch up.

**The binding constraint is assignment.** The rules forbid writing code or opening a PR before a
maintainer assigns you. As of Oct 26, maintainers seem to have stopped accepting or assigning new
issues since about Oct 19 (details in §1). The plan therefore:
1. spends today getting assigned (at most 2 requests),
2. prepares everything the rules allow while waiting,
3. builds fast, but to the reviewer's standard, only after assignment.

**Kill switch.** If no assignment has arrived by **Thu Oct 30, 12:00 IST**, don't build. A PR
opened without assignment can get you banned from every future WeMakeDevs event.

**Odds, honestly.** Getting assigned at all is uncertain. If you get assigned and the PR meets the
standard below, the chance of a merge is decent, though it will probably land in November.
Few people have a merged PR so far, so a merged PR has good odds in the $100 draw.

---

## 1. Facts as of 2026-10-26 (checked; ⟳ = re-check before acting)

Sources: WeMakeDevs overview, rules and resources pages; GitHub pages for
`topoteretes/cognee` and `topoteretes/cognee-community`; the cognee 1.6.5 wheel from PyPI.

**Where things go**
- Issues live in `topoteretes/cognee`. Data-source connector code goes in
  `topoteretes/cognee-community` under `packages/connector/<name>/`. Branch from `main` there.
- To request assignment, comment on the issue and tag **@NMZivkovic**. The toolkit says the comment
  must cover: (1) where you'll read from (API/SDK, how you authenticate), (2) what data goes into
  Cognee and its shape, (3) how you'll test against a **real** account. If an assignee hasn't
  touched an issue "for a while", the toolkit says you may tag them.
- Rules: you may open at most 5 new integration issues, have at most 5 PRs open, and must write a
  blog post per PR. Don't ping maintainers to review or merge. All code and writing must be your
  own; AI assistance is allowed, AI-generated PRs are not. Prizes go to the GitHub account that
  authored the PR. The draw only counts merged PRs that were **submitted through the WeMakeDevs
  form** (the form is "opening soon").

**What's merged**
- `cognee-community` `main` has 9 connectors: apollo, asana, confluence, gmail, google-calendar,
  google-drive, notion, onenote, slack.
- cognee core 1.6.5 ships its own connectors too: gmail, google_calendar, google_drive, linear,
  notion. The core team merged an Obsidian connector into core on Oct 22 (cognee PR #6241). Always
  check core for duplicates.
- New connectors merged in October:
  - Google Calendar #370: merged Oct 15 (its main commit is dated Oct 11).
  - Apollo #304: merged Oct 19, 65 comments.
  - OneNote #301: merged Oct 20.
  - Asana #349: merged Oct 21 (first commit Oct 9), 37 comments, 3 review rounds.
- Nothing has merged since Oct 21. ⟳

**Queue and review capacity**
- `cognee-community` has **320 open PRs**. ⟳
- Connector PRs are reviewed and merged by **goran-radonic**. He has reviewed 22 PRs: 3 merged,
  19 still open with 15–77 comments each.
- One account opened more than 20 connector PRs on Oct 25–26. That's the spam pattern; never
  imitate it.

**Assignment status** ⟳
- There are 156 open issues labeled INTEGRATIONS + hackathon. Only **2** are unassigned, and both
  are poor targets:
  - #4811 Reddit: needs approved Reddit Data API access. The last PR was rejected, and 15+ requests
    are pending.
  - #4728 Evernote: legacy Thrift API with OAuth 1.0a. The last PR was rejected for testing only
    against fakes.
- dexters1 accepted and assigned issues in batches on **Oct 7, Oct 13 and Oct 19**. **No issue
  created after Oct 19 has the `hackathon` label.** Dozens of proposals from Oct 20–26 have no
  maintainer reply (example: #6321).
- Acceptance is selective. Some early-October proposals still haven't been accepted (no
  `hackathon` label): Hypothes.is #5437, MLflow #5582, OpenReview #5646, Hugging Face Hub #5347
  and #5795. Accepted proposals lean toward
  team and company tools: helpdesk, LMS, chat, commerce, CI (the theme is "a company brain").
- Most tools are already proposed (737 open issues). Every candidate checked during planning was
  taken: Zotero, Raindrop, Hypothes.is, MLflow, OpenReview, YouTrack, GitBook, Zulip, Taiga,
  Forgejo/Gitea, BookStack, Canny, Fider, Tally, Logseq, Obsidian, Anytype, Cal.com, Hugging Face,
  Todoist.
- Many assigned issues have assignees who went quiet, and competing PRs from people who were never
  assigned. Example: Todoist #4815, where the assignee has been silent since Oct 3 and three other
  people have open PRs.
- Re-checked later on Oct 26: still 0 hackathon-labeled issues created after Oct 19, and still
  only those 2 unassigned issues, even counting issues labeled `hackathon` alone.

**Discord #contributions** (Vividh's screenshots, Oct 26)
- On Oct 24 another participant asked exactly our process question: are new Path B proposals still
  being reviewed, and is any extra eligibility step needed? Two days later there was no visible
  maintainer reply.
- Several participants post PR links and @-mention dexters1 or Vasilije asking for review or
  assignment, with no visible maintainer replies. That's the pinging the rules forbid.
- A PR opened Oct 12 for an assigned issue (cognee-community #373) still had 0 comments and 0
  reviews on Oct 20.
- At least one connector PR was opened against the wrong repo (cognee #6040, Meta Ads).
- An "extra income opportunities, DM me" message was posted on Oct 25: a scam. Never DM such
  accounts.
- Not checked yet: #announcements, pinned messages, and a server search for maintainer posts.

**What the reviewer demands**

From goran-radonic's first-round review of Asana PR #349, plus his rejections of the Evernote and
Reddit PRs. §14 turns this into a checklist.
- Test against the **real API**. The Evernote PR was rejected because it only used fakes and had
  wrong endpoints and types.
- Correct incremental cursor. The Reddit PR had none.
- A failed run must never forget live documents. The Reddit PR's `replace` dropped live posts.
- An empty selection must not delete everything.
- Pagination must be bounded.
- Missing ids and wrongly shaped bodies (for example an HTML login page) must not end as a quiet
  success.
- The token must never appear in logs or errors.
- A 401 or 429 mid-run must stop cleanly and resume next run.
- Items that leave the selected scope must be forgotten (another Evernote miss).
- Accurate README.
- No unreachable asserts or needless `ImportError` wrappers.
- Tests that raise specific exceptions, not `pytest.raises(Exception)`.
- The PR must go to the right repo. The Reddit PR went to core.

**What the merged Asana PR description contained**
- `Closes topoteretes/cognee#N`
- design bullets
- "Where this differs" from the issue
- "Verified against a real workspace" table, dated, separating what was tested live from what was
  tested only with mocks
- logs of an example run (an edit and a delete)
- pytest and ruff output with versions
- the DCO affirmation, plus `Signed-off-by` on every commit

**Cognee contract** (read from the cognee 1.6.5 source, `cognee/tasks/ingestion/`)
- `dlt_utils.DOCUMENT_SOURCE_ATTR = "cognee_document_source"`. Setting it on the dlt
  resource/source routes each row as a text document through cognify.
- `dlt_utils.PIPELINE_SCOPE_ATTR = "cognee_pipeline_scope"`. It gives incremental state its own
  pipeline. Set it to `resource_name`.
- `dlt_utils.guarded_rows(rows, check_active)`. It wraps the row iterator so a host can stop the
  sync by raising.
- Document rows are read as **`title`**, **`content`**, `url` and `id`, plus an optional
  `cognee_node_set` (a JSON list). The text stored is `"# {title}\n\n{content}"`. The column is
  `content`, not `text`.
- Document sources honor `write_disposition`:
  - `replace` (snapshot: the Notion and Slack connectors)
  - `merge` plus a `_deleted` column with `hard_delete: True` (tombstones: the Asana, Google
    Calendar and Apollo connectors)
- Orphan cleanup is scoped to the tables that were loaded. An incremental run with no load jobs
  deletes nothing.
- Unchanged content keeps its content-hash data_id, so it isn't re-cognified. Keep volatile fields
  out of `title`/`content`.
- Latest cognee: 1.6.5 (Oct 16); 1.6.6rc1 (Oct 23). Recent connectors pin `cognee>=1.6.2` or
  `>=1.6.3`, `<2`.

**Correction to the earlier chat answer.** Leaders don't have 5+ merged PRs; they have about 1
each. The conclusion still holds: go for one or two strong PRs and the $100 draw, not Top
Contributor.

---

## 2. Hard rules (any violation can mean a ban)

1. **No connector code and no PR before assignment.** Before writing any code, the executor checks
   the issue page shows `VividhDesign` under Assignees.
2. **At most 2 assignment requests at a time.** Only ask for issues you'll actually build. If you
   can't deliver one, comment that you're stepping back so it frees up.
3. **No pinging** to review, merge or assign, on GitHub or Discord. Many participants @-mention
   maintainers in #contributions with PR links; don't copy them. Never DM accounts offering money
   or "opportunities".
4. **The human owns everything public**: issue comments, the PR description, replies to reviews,
   the blog post. The executor drafts structure and checks facts; Vividh writes or rewrites the
   text in his own words and posts it.
5. **The human understands every line.** Before committing, Vividh must be able to explain the code
   without notes (the §9.11 gate).
6. **Right repo and path:** `topoteretes/cognee-community`, `packages/connector/<slug>/`, branched
   from `main`.
7. **DCO:** every commit signed off with Vividh's real name and an email verified on GitHub. The PR
   description ends with the exact DCO affirmation (§10).
8. **Originality:** follow patterns from merged connectors but write your own implementation. Never
   copy from other contributors' open PRs. Never fabricate test results or claims of live testing.
9. **One public blog post per PR**, about real use. Submit the PR and blog link through the
   WeMakeDevs form.

---

## 3. Who does what

| Task | Vividh (human) | Executor (Claude) |
|---|---|---|
| Discord check, process question | ✅ | |
| List the tools you actually use | ✅ | |
| Research targets, check duplicates, score them | decides | ✅ |
| Assignment comment / Path B issue | writes and posts | outline, fact-check |
| Fork the repo | ✅ (GitHub UI) | attaches and clones the fork |
| Real accounts, seed data, tokens, LLM key | ✅ (tokens as environment secrets, never in chat) | |
| Check the API with read-only calls | | ✅ |
| Design note | reviews | ✅ drafts |
| Code, tests, README, example | reviews every file | ✅ after assignment |
| Live run against the real account | present, does the UI edits and deletes | runs the scripts |
| Understanding gate (walkthrough + quiz) | ✅ must pass | ✅ runs it |
| Commit with sign-off, push to fork | approves identity and content | ✅ |
| Open the PR | ✅ (GitHub UI, own words) | drafts the evidence sections |
| Blog post | ✅ writes it | outline, accuracy review |
| WeMakeDevs submission form | ✅ | |
| Review rounds (November) | replies | fixes, re-tests |

---

## 4. Timeline (IST)

| When | What | Gate |
|---|---|---|
| Sun Oct 26 (today) | Phase 0 (situation check) → Phase 1 (pick targets) → Phase 2 (post requests by ~18:00 IST) | Requests posted |
| Mon Oct 27 to Wed Oct 29 | Phase 3 prep; check the issue pages for assignment morning and evening | Prep done by Oct 28 evening |
| On assignment | Phase 4 build: 1.5–2 days; aim to open the PR within 36 h of assignment | Gates §9.10 and §9.11 |
| Thu Oct 30, 12:00 | **Kill switch:** no assignment means no build | |
| Thu Oct 30 (assigned late) | Build only if Phase 3 is fully done and the simple snapshot model fits; otherwise step back | |
| Fri Oct 31, by 12:00 | Latest moment to open the PR (the deadline's timezone isn't stated, so leave a buffer) | PR open |
| Fri Oct 31 | Blog published, PR and blog submitted via the form (if it's open) | |
| November | Review rounds: reply within 24 h, fix root causes, never ping | |

---

## 5. Phase 0: situation check (today, ≤ 30 min)

**0.1 Vividh: Discord.** #contributions was checked on Oct 26 (see §1).
- **Don't post the process question.** Another participant already asked it on Oct 24 and got no
  reply. If you want, add a 👍 reaction to that message; don't post a duplicate.
- Still to check:
  - #announcements;
  - pinned messages in #contributions and #announcements (the pin icon in the channel header);
  - a server search for `Mergetober`, and for posts from the maintainers' handles (for example
    `from:` Dexters1).
- Send the executor screenshots of anything a maintainer posted about acceptance, assignment or
  the deadline.

**0.2 Executor: re-check the facts** (WebFetch):
- `https://github.com/topoteretes/cognee/issues?q=is%3Aissue%20label%3Ahackathon%20created%3A%3E2026-10-19`.
  More than 0 results means acceptance has resumed.
- `https://github.com/topoteretes/cognee/issues?q=is%3Aissue%20is%3Aopen%20label%3AINTEGRATIONS%20label%3Ahackathon%20no%3Aassignee`.
  Lists unassigned labeled issues.
- `https://github.com/topoteretes/cognee-community/pulls?q=is%3Apr%20is%3Amerged%20sort%3Aupdated-desc`.
  Shows merge activity.

**0.3 Vividh tells the executor:**
- 5–10 tools you **actually use** or will genuinely start using for real work: project, lab, team,
  course, OSS-community or documentation tools.
- Whether you have, or can get, an LLM API key with a small spending cap. You need it for the live
  run, because cognify calls an LLM.

**Decision**
- Discord says no new assignments at all: stop the plan.
- Discord says no new issues: drop Track B and do only Track A.
- **No official word (the situation on Oct 26):** do both tracks, but cap today at about 3 hours
  (Phase 1 + 2). Do account and API prep only for the targets you actually requested. Do the
  generic prep (fork, toolchain, reading reference connectors) only if you'd value it for learning
  anyway.

---

## 6. Phase 1: pick at most two targets (executor, ~2–3 h)

Use WebFetch for public GitHub pages. Git clone works anonymously. The GitHub API isn't available
for topoteretes repos in this session, so don't try to work around that.

### Track A: take over an issue whose assignee went quiet (the toolkit allows this)

- **A1.** Page through the labeled issues:
  `https://github.com/topoteretes/cognee/issues?q=is%3Aissue+is%3Aopen+label%3AINTEGRATIONS+label%3Ahackathon&page=N`
  for N = 1..7. Keep tools that:
  - have a free account and an instant API token (no sales call, no app review),
  - hold rich text (tickets, docs, messages, comments),
  - Vividh can genuinely use.
- **A2.** For each kept issue (stop after about 15 checked), open the issue page and record:
  - the assignee and assignment date,
  - the assignee's last comment date,
  - whether the assignee has a PR for it:
    `https://github.com/topoteretes/cognee-community/pulls?q=is%3Apr+author%3A<assignee>`,
  - competing PRs: `https://github.com/topoteretes/cognee-community/pulls?q=is%3Apr+<tool>`,
  - how many takeover requests are already pending.
- **A3.** It qualifies only if:
  - it was assigned at least 10 days ago,
  - the assignee has no PR for it and has been silent at least 10 days,
  - there are **0** competing open PRs (1 at most),
  - there are at most 3 pending requests.

### Track B: one new Path B proposal

- **B1.** Start from Vividh's list in 0.3, then add company-brain tools with free tiers.
- **B2.** Every one of these duplicate checks must return zero hits:
  - cognee issues, all states: `https://github.com/topoteretes/cognee/issues?q=<tool>`, plus a
    variant with `in:title`;
  - cognee-community PRs: `https://github.com/topoteretes/cognee-community/pulls?q=<tool>`;
  - cognee core PRs: `https://github.com/topoteretes/cognee/pulls?q=<tool>`;
  - core's connector list: `cognee/tasks/ingestion/connectors/` in the latest cognee release;
  - `packages/connector/` in the cognee-community clone;
  - `topoteretes/cognee-integrations`.
- **B3.** Check access:
  1. Vividh creates a free account and token.
  2. The executor checks the API host is reachable from the container:
     `curl -sS -o /dev/null -w '%{http_code}' https://<api-host>/`.
  3. The executor makes 3–5 **read-only** GET calls.
  4. Record pagination, rate-limit headers, how changes are detected (updated_since, a sync token,
     or webhooks only) and how deletions show up (tombstones, `is_deleted`, or items simply
     vanishing).
- **B4.** Keep the tool only if it has zero duplicates, a real free account, text-rich content and a
  clear sync story.

### Score and decide

The executor fills in a table:

| Candidate | Track | Access (0–3) | Simple sync (0–3) | Competition (0–3) | Genuine use (0–3, Vividh) | Company-brain fit (0–2) | Notes |
|---|---|---|---|---|---|---|---|

Recommend the best one per track. **Vividh picks at most 2 in total.** Prefer the tool with the
simplest API that still syncs correctly: simpler code means fewer review rounds.

---

## 7. Phase 2: ask for assignment (Vividh, today, before ~18:00 IST)

Vividh writes these in his own words. The executor only checks that each required point is covered
and every claim is true.

**Takeover comment.** Cover, in order:
- A friendly tag to the assignee: are they still working on it? State the facts: assigned on
  <date>, no PR yet.
- Say you'll step back if they are.
- Tag @NMZivkovic: if they've moved on, could the issue be reassigned to you?
- The three required points: data source and auth; what goes into Cognee and its shape (one
  document per X, including Y); how you'll test against a real account.
- "I won't write code until I'm assigned."

**Path B issue.** Use the Feature Request template (blank issues are disabled). Title:
`Hackathon [Feature]: Add <Tool> data-source connector`. Accepted proposals (Zoho Desk #6034,
Canvas LMS #5972) used these sections:
- **Problem Statement**: what knowledge lives in the tool, the gap in Cognee, and a note that you
  searched for duplicates.
- **Proposed Solution**: `packages/connector/<slug>/` in cognee-community, with Authentication
  (read-only scope), Selecting what to ingest, Documents (one per entity, with its comments),
  Incremental sync, Deletion handling.
- **Watch out for**: pagination, rate limits, personal data, API quirks you actually observed.
- **Alternatives Considered**
- **Use Case**: 2–3 concrete questions an agent could then answer.
- **Implementation Ideas**: **verified API findings with the date** (from B3), plus the package
  tree.
- **Acceptance Criteria**: a checklist. Connect and select; ingested and searchable; only changes
  re-synced; upstream deletions forgotten; README and runnable example; tests.
- **Additional Context**: "Mergetober, Path B: I'd like to build this. I won't write code until
  assigned." Your test plan against a real account. Tag @NMZivkovic.
- Tick the template's checkboxes truthfully.

After posting, don't follow up on GitHub. If nothing happens in 48 h, at most one polite Discord
message.

---

## 8. Phase 3: prepare while waiting (allowed; no connector code)

- **3.1 Fork and attach.**
  1. Vividh forks `topoteretes/cognee-community` in the GitHub UI.
  2. The executor calls `add_repo(owner="VividhDesign", repo="cognee-community", access="push")`
     and clones where the tool says.
  3. `git remote add upstream https://github.com/topoteretes/cognee-community && git fetch upstream main`.
- **3.2 Check the toolchain.** In the fork, in `packages/connector/google-calendar/`:
  `uv sync --locked --group dev`, `uv run --frozen pytest tests -ra`,
  `uvx ruff check .`, `uvx ruff format --check .`. That package's dev group has no ruff, so use
  `uvx` here.
  - Auto mode blocked running external repo code during planning. Ask Vividh to approve the prompt
    or add a permission rule; don't work around it.
- **3.3 Study these files and keep short notes** in the scratchpad (connector paths are under
  `packages/connector/`):
  - `notion/…/notion.py` plus its tests: the snapshot model; aborting on errors; `_is_gone`
    vs `_is_transient`.
  - `slack/…/slack_export.py`: a snapshot of local files.
  - `google-calendar/…/google_calendar.py` plus all three test files: a sync token plus tombstones,
    the 410 → full resync, refusing an empty selection, forgetting a calendar dropped from the
    config, and `test_google_calendar_forget.py` (a graph-level forget test with a mocked LLM and
    mocked embeddings). This is the best overall reference.
  - `asana/…/asana.py` plus its README sections "When Asana fails part of the way through" and
    "Verified against a real workspace vs. taken from the docs".
  - `apollo/tests/` for the split layout with a fake API module.
  - cognee core: `cognee/tasks/ingestion/dlt_utils.py` and `resolve_dlt_sources.py`
    (`_build_document_data_item`, document cleanup). Get them by downloading the cognee wheel or
    doing a sparse clone.
- **3.4 Real account (Vividh).** Seed realistic data that reflects genuine use: at least 10 items,
  some with comments, one you'll edit and one you'll delete later. Create a **read-only** token.
  Add it, and later the LLM key, as **environment secrets** for this cloud environment
  (`read_documentation(topic="environment.secrets")` shows how), never in chat.
- **3.5 Check the API (executor, read-only calls).** Confirm endpoints, field names, pagination,
  error bodies, rate-limit headers, and change and deletion semantics against the real account.
  Save the notes in the scratchpad.
- **3.6 LLM key.** Vividh sets `LLM_API_KEY` (plus provider and model variables if not using
  OpenAI) with a spending cap. The executor confirms the provider's API host is reachable. If a
  host is blocked, see `read_documentation(topic="environment.network")`, or run the live parts on
  Vividh's own machine.
- **3.7 Design note** (executor drafts, Vividh reviews; not code). Cover:
  - document ids,
  - what each document contains,
  - the sync model (§9.4),
  - how deletions are detected,
  - state keys,
  - what happens on each failure type,
  - limits,
  - the test matrix from §9.6.
- **3.8 Blog prep (Vividh).** Write down your real use case and 3 questions you'd ask your data.
- **3.9 Check twice a day** (WebFetch the issue page) whether you've been assigned. Don't ping.

---

## 9. Phase 4: build after assignment

**9.0 Gate.**
- The issue page shows `VividhDesign` under Assignees. Record the URL here.
- Start the clock; aim to open the PR within 36 h.

**9.1 Branch.**
`git checkout -b feat/<slug>-connector upstream/main`. Use lowercase-hyphen `<slug>` for the folder
and `<slug_u>` (underscores) for the Python name.

**9.2 Files.** Touch nothing outside this folder unless a reviewer asks.
```
packages/connector/<slug>/
├── README.md
├── pyproject.toml
├── uv.lock                          # committed, like every other connector
├── cognee_community_connector_<slug_u>/
│   ├── __init__.py                  # from .<slug_u> import <slug_u>_source; __all__ = [...]
│   └── <slug_u>.py
├── examples/example.py
└── tests/
    ├── fake_<slug_u>.py             # in-memory fake of the API (pattern: fake_calendar.py)
    ├── test_<slug_u>_source.py      # config, markers, auth, empty selection
    ├── test_<slug_u>_sync.py        # rendering, pagination, retries, cursor, deletions, failures
    └── test_<slug_u>_forget.py      # end-to-end through cognee with mocked LLM/embeddings
```

**9.3 `pyproject.toml`** (follows asana, google-calendar and apollo):
```toml
[project]
name = "cognee-community-connector-<slug>"
version = "0.1.0"
description = "<Tool> data-source connector for cognee: sync <what> into memory (incremental + forget-on-delete)"
readme = "README.md"
requires-python = ">=3.11,<3.14"
dependencies = [
    # Needs document-mode routing (DOCUMENT_SOURCE_ATTR), table-scoped orphan cleanup,
    # PIPELINE_SCOPE_ATTR and guarded_rows (cognee 1.6.3 and later 1.x releases).
    "cognee>=1.6.3,<2",
    "dlt[sqlalchemy]>=1.9.0,<2",
    "requests>=2.31.0,<3",
]

[dependency-groups]
dev = ["pytest>=8,<9", "pytest-asyncio>=0.23,<2", "ruff>=0.13,<1"]

[project.urls]
Homepage = "https://github.com/topoteretes/cognee"
Repository = "https://github.com/topoteretes/cognee-community"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["cognee_community_connector_<slug_u>"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "B", "UP", "C4", "PGH", "SIM", "RUF"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
```

**9.4 Pick the sync model.** Choose the simplest one the API supports correctly.

| What the API offers | Model | Reference |
|---|---|---|
| A sync token or `updated_since`, **and** a deletion signal (tombstones, `is_deleted`, cancelled status) | `merge` + `_deleted` tombstones; state = cursor (+ known ids) | google-calendar |
| `updated_since` but deletions just vanish; cheap to list every id | `merge` for changes + an id sweep each run; confirm each "missing" item with a direct GET that returns 404 before tombstoning | asana (only what you need) |
| No change feed and a small corpus | `replace` snapshot; abort the whole run on any error | notion, slack |

**9.5 Implementation requirements.** Each one maps to a review finding.
- **Factory.** `<slug_u>_source(token=None, <selection>=None, *, resource_name=<TABLE>, check_active=None, client=None)`.
  - The token falls back to the `<TOOL>_…` environment variable.
  - Validate eagerly: missing token → `ValueError` naming the env var; empty or invalid selection →
    `ValueError`. Never resolve to "everything forgotten".
  - Validate `resource_name`: non-empty, ≤64 characters, unchanged by dlt's snake_case
    normalization (see asana's `_check_resource_name`).
  - Check `hasattr(dlt_utils, "PIPELINE_SCOPE_ATTR") and hasattr(dlt_utils, "guarded_rows")`. If
    either is missing, raise a `RuntimeError` that names the same floor as `pyproject.toml`
    (**cognee>=1.6.3**). The reviewer flagged a guard that named the wrong version.
- **Resource.**
  - Incremental:
    `@dlt.resource(name=resource_name, primary_key="id", write_disposition="merge", columns={"_deleted": {"data_type": "bool", "hard_delete": True}})`.
  - Snapshot: `write_disposition="replace"`.
  - Body: `yield from dlt_utils.guarded_rows(_rows(...), check_active)`.
  - Then `setattr(resource, DOCUMENT_SOURCE_ATTR, "<slug_u>")` and
    `setattr(resource, dlt_utils.PIPELINE_SCOPE_ATTR, resource_name)`.
  - Optionally `resource.cognee_sync_stats = stats` (scanned / changed / deleted / skipped).
- **Rows.**
  - Live: `{"id": f"<slug_u>:<kind>:<native_id>", "title": …, "content": <markdown>, "url": <permalink>, "_deleted": False}`.
  - Tombstone: `{"id": row_id, "_deleted": True}`.
  - Ids are deterministic and unique across the containers you select.
- **Content.**
  - One document per logical entity, with its children (for example a ticket plus its comments)
    in a fixed order.
  - Include people, project and container names so entity extraction links them.
  - **Leave volatile fields out of `title`/`content`** (updated_at, counters, view counts), or the
    content hash changes on every run.
  - Convert HTML to plain text where needed.
- **HTTP.**
  - One session with a 30 s timeout.
  - Retry 429, 5xx, timeouts and connection errors, honoring `Retry-After`. Cap any single wait at
    60 s and the run's total waiting at about 120 s; past that, stop cleanly.
  - Permanent errors raise a typed `<Tool>APIError(status, endpoint)`. The message has the status
    and endpoint only, never the token or a response body.
  - Strip whitespace and newlines from the token, and never echo it.
- **Shape and termination.**
  - A non-JSON or wrongly shaped 200 response raises `<Tool>ResponseError`.
  - Read ids with `.get()`; skip and log an item with no id.
  - Bound pagination with a max page count and by detecting a repeated cursor.
- **State (merge).**
  - Keep the cursor, known ids and per-container state in `dlt.current.resource_state()`.
  - Advance the cursor **only after the full round succeeded**.
  - An expired cursor triggers a full listing reconciled like a snapshot.
  - A container removed from the selection forgets its documents.
  - Any error mid-run raises: **nothing is deleted and the cursor doesn't move**.
- **Snapshot (replace).**
  - Never yield a partial snapshot; any error aborts the run.
  - Treat an item as gone only on a definite 404 for an explicitly selected item.
- **Hygiene.** No unreachable asserts, no needless `ImportError` wrappers. Keep the module
  docstring short (≤ ~15 lines); the details go in the README.

**9.6 Tests.** All offline. Use specific exception types. Each test name says what it proves.
1. The source sets the document-mode marker (`document_source_tag(source) == "<slug_u>"`) and
   `PIPELINE_SCOPE_ATTR`.
2. A missing token gives a clear error when the source is built. A token with a trailing newline
   never appears in logs or errors (use `caplog`).
3. An empty selection is refused, not treated as "forget everything".
4. Row shape and rendering: id, title, content, url, children in a fixed order, no volatile fields.
5. Pagination follows the cursor, stops at the last page, and raises on a repeated cursor or past
   the page cap.
6. A 429 with `Retry-After` is retried and then succeeds. 5xx and timeouts retry. Exhausted retries
   raise `<Tool>APIError`. Inject a fake sleep so tests are fast.
7. A non-JSON or wrongly shaped body raises `<Tool>ResponseError`.
8. The first sync yields everything and saves the cursor. A re-sync with no changes yields nothing
   (merge) or the same stable rows (replace).
9. An edit yields the document again with the new content.
10. An upstream delete produces a tombstone (merge) or the row is absent (replace).
11. An error on a later page raises, leaves state and cursor untouched, and produces no tombstones.
12. An expired cursor resyncs like a snapshot and tombstones what vanished.
13. A container dropped from the selection, or an item moved out of scope, is forgotten.
14. dlt pipeline test into a temporary sqlite destination,
    `dlt.destinations.sqlalchemy(f"sqlite:///{db}")` with `pipelines_dir=tmp_path/"state"` (Notion
    pattern): rows appear, edits replace, deletes disappear from staging.
15. **Graph-level forget test** (google-calendar `test_google_calendar_forget.py` pattern):
    - real `cognee.add(...)` + `cognee.cognify(...)` with a mocked
      `LLMGateway.acreate_structured_output`, mocked `LiteLLMEmbeddingEngine.embed_text`, no-op
      indexing, sqlite, and temporary data and system roots;
    - give each item one distinctive token;
    - after a delete and re-sync, that token is gone from the graph and the others remain.

**9.7 README** (headings follow google-calendar and asana):
- Title + one-line pitch
- Requirements (cognee ≥ 1.6.3)
- Install
- Setup: account, read-only token, env vars
- Usage: the `cognee.remember(...)` call; for merge, pass `primary_key="id"`,
  `write_disposition="merge"`, `max_rows_per_table=0`
- Selecting what to ingest
- What a document looks like (a short sample)
- How incremental sync works
- How forget-on-delete works
- When <Tool> fails part of the way through
- Limits
- Privacy (opt-in, what's read, using a dedicated dataset)
- Verified against a real account vs. taken from the docs
- Testing

Every sentence must be true of the code, including any request counts.

**9.8 `examples/example.py`** (the asana example's shape):
- A docstring with privacy notes and one-time setup.
- Read the env vars and print a hint if they're missing.
- `cognee.remember(...)` with the right kwargs, then print the sync stats.
- `cognee.search(query_text=..., query_type=cognee.SearchType.GRAPH_COMPLETION, datasets=[...])`.
- Tell the user to edit or delete something and re-run.

**9.9 Lock, lint, build** (in the package folder):
```bash
uv lock && uv sync --locked --group dev
uv run --frozen pytest tests -ra
uv run --frozen --with 'cognee==1.6.3' python -m pytest tests -ra   # the supported floor (OneNote CI pattern)
uv run --frozen ruff check . && uv run --frozen ruff format --check .
W=<session scratchpad>/wheelcheck   # use the scratchpad, not /tmp
uv build && uv venv "$W" && uv pip install --python "$W/bin/python" dist/*.whl \
  && (cd "$W" && "$W/bin/python" -c 'import cognee_community_connector_<slug_u>')
```
Also run `uvx ruff check . && uvx ruff format --check .` from the repo root (CI runs ruff across
the repo). Don't commit `dist/`.

**9.10 Live check against the real account** (Vividh present; gate).
1. With the token and `LLM_API_KEY` set, run `uv run python examples/example.py`. Record the stats
   and the answer.
2. In the tool's UI, Vividh edits item A, deletes item B, and moves item C out of the selected
   scope (or drops a container from the selection).
3. Re-run. Confirm the stats show A changed and B and C forgotten, and that search no longer
   reflects B or C.
4. Optional: revoke the token and re-run. You should get a clean error and nothing deleted.
5. Fill in the "Verified against a real account (date)" table: behavior | live | mock only. Only
   rows that really ran count as live. Redact tokens and any personal data.

**9.11 Understanding gate** (gate).
- The executor walks Vividh through each file.
- Vividh answers without notes:
  - Where does the data come from, and how does it authenticate?
  - Why is a document id stable?
  - If page 3 returns a 500, is anything deleted? Does the cursor move?
  - How does a deleted item leave Cognee's graph? (tombstone → hard delete in staging → orphan
    cleanup)
  - Why aren't timestamps in `content`?
  - What do `check_active` and `PIPELINE_SCOPE_ATTR` do?
- Vividh changes anything he wouldn't have written himself, and writes the README intro and the
  PR text in his own words.
- No commit until he passes.

**9.12 Commit and push.**
- `git config user.name "<Vividh's real name>"` and `git config user.email "<email verified on GitHub>"`.
  The author email must match the sign-off.
- `git commit -s -m "feat(connector): add <Tool> data-source connector"`. Only after Vividh
  approves; the sign-off is his DCO certification.
- `git push -u origin feat/<slug>-connector` (pushes to the fork).
- By default, commits the executor makes carry a `Co-Authored-By: Claude` trailer. The rules allow
  AI assistance; keeping the trailer is Vividh's call.

---

## 10. Phase 5: open the PR (Vividh, in the GitHub UI)

From the fork's branch, use "Compare & pull request" against `topoteretes/cognee-community:main`.
Title: `feat(connector): add <Tool> data-source connector`. Keep the repo template's two headings.
Body skeleton (Vividh writes the prose; the executor supplies the evidence blocks):

```markdown
Closes topoteretes/cognee#<N>

## Description
- Auth: …
- Selection: …
- Documents: …
- Incremental sync: …
- Forget-on-delete: …
- When <Tool> fails part of the way through: …
- Packaging: cognee>=1.6.3,<2; uv.lock included.

### Where this differs from the issue
1. …

### Verified against a real <Tool> account (<date>)
| Behavior | Live | Mock only |
|---|---|---|

### Example run
<first sync → edit + delete → second sync; redacted logs>

### Tests
<pytest -ra summary, the cognee==1.6.3 floor run, ruff check, ruff format --check; Python/uv versions>

## DCO Affirmation
I affirm that all code in every commit of this pull request conforms to the terms of the Topoteretes Developer Certificate of Origin.
```

- Leave "Allow edits by maintainers" on.
- If the ruff CI goes red, fix it and push.
- Don't ping anyone. Don't comment "please review".

---

## 11. Phase 6: blog post and submission (Vividh)

- Write it yourself on dev.to, Medium, Hashnode or your own blog, about **how you actually use it**:
  1. the real problem in your work,
  2. what the connector does,
  3. setup in about 5 commands,
  4. a real run on your data with a real question and the actual answer,
  5. in plain words: how sync and forget-on-delete keep memory correct, and what happens on
     failure,
  6. limits and what you learned,
  7. links to the issue and PR.
- The executor reviews it **for technical accuracy only**.
- Publish within 24 h of opening the PR, ideally by Oct 31.
- Submit the PR and blog link through the WeMakeDevs form as soon as it opens. Check
  https://www.wemakedevs.org/hackathons/mergetober daily; your PR should also appear on your
  dashboard.

---

## 12. Phase 7: review rounds (November)

- Reply to every review within 24 h. Reply on each thread saying what changed, or why not.
- Fix the root cause, not the symptom. Add a test for every finding.
- Re-run the full §9.9 checks before each push, and §9.10 if behavior changed.
- Keep the PR description accurate. Update "Where this differs" and the verification table.
- Never ping to speed things up. A merge can come after Oct 31; it counts once it's merged.

---

## 13. Contingencies

| Situation | Action |
|---|---|
| No assignment by Thu Oct 30, 12:00 IST | Stop. Don't build or open a PR. Leave your proposal up. |
| Assigned between Oct 30 12:00 and 23:59 IST | Build only if Phase 3 is complete and the snapshot model fits. Otherwise comment that you're stepping back. |
| Both requests get assigned | Build the simpler one first. Do the second only if the first PR is open by Oct 29 and there's time to meet the same standard; otherwise release it politely. |
| The original assignee comes back on a takeover | Thank them and step back. |
| A maintainer rejects or closes the Path B issue as a duplicate | Accept it; don't argue. |
| The API host is blocked from the container | `read_documentation(topic="environment.network")`, or run the live steps on Vividh's machine and paste redacted output. |
| `uv` or `pytest` blocked by permissions | Vividh approves the prompt or adds a permission rule. No workarounds. |
| No LLM key | Get one with a small cap before 9.10. The live search answer is the strongest evidence. |
| CI red after opening | Reproduce locally, fix, push. Never skip or disable a test. |
| Reviewer asks for a large redesign | Do it properly; ask Vividh first if it changes the scope agreed in the issue. |

---

## 14. Reviewer checklist (all must be true before opening the PR)

- [ ] Correct repo and path; only `packages/connector/<slug>/` changed; `uv.lock` committed.
- [ ] `content`/`title`/`url`/`id` rows; the document marker and `PIPELINE_SCOPE_ATTR` set;
      `guarded_rows` + `check_active` wired.
- [ ] Tested live against a real account; the dated verification table separates live from mocks.
- [ ] Endpoints, field names, pagination and error codes confirmed against the real API, not just
      the docs.
- [ ] The cursor advances only after a full successful round; an expired cursor triggers a full
      reconcile.
- [ ] Upstream deletes and out-of-scope items are forgotten (dlt test + graph-level test).
- [ ] No failure path forgets live data; an empty selection is refused.
- [ ] Bounded pagination; repeated cursor detected.
- [ ] Wrongly shaped bodies and missing ids handled loudly, not as a quiet success.
- [ ] The token never appears in logs, errors, README, PR or blog.
- [ ] Retries honor `Retry-After` with caps; a mid-run 401 or 429 stops cleanly and resumes next run.
- [ ] Volatile fields kept out of content; output order fixed.
- [ ] Specific exception types in tests; all §9.6 tests present and passing.
- [ ] `ruff check` and `ruff format --check` clean (package and root); the wheel builds and imports.
- [ ] README claims match the code; the example runs.
- [ ] Every commit has `Signed-off-by: <Vividh>`; the PR ends with the DCO affirmation.
- [ ] Vividh passed the §9.11 gate and wrote the public text himself.

---

## 15. Executor operating rules

1. Never post comments, issues, reviews or PRs on `topoteretes/*`. Draft for Vividh only.
2. Never push to `topoteretes/*`. Push only to `VividhDesign/cognee-community`, after Vividh
   approves.
3. No connector code before 9.0 passes (assignment checked on the issue page).
4. Keep secrets out of chat, logs, files, commits, the PR and the blog. Use the env vars Vividh sets.
5. Read topoteretes GitHub pages with WebFetch. Use anonymous `git clone` for code. Don't try to
   get API access to their repos.
6. Ask before installing dependencies or running tests from external repos if prompted. Never work
   around a denial.
7. Explain each file to Vividh. Run the §9.11 gate before any commit.
8. Never claim a test or live result that didn't run. Paste real output.
9. Never draft more than 2 assignment requests at a time. Never suggest opening many PRs.
10. Write code in the style of the merged connectors: line length 100, ruff rules as in 9.3, the
    comment density of google-calendar and asana.

---

## 16. Claims from the earlier Gemini answer to ignore

- The "Path A triage" picks (#6034 Zoho Desk, #5972 Canvas, #5836 WhatsApp, #5814 Google Forms…)
  are **all assigned** already.
- Rows use `content` (+ `title`), not `text`. You don't need a `content_hash` column; cognee hashes
  the content.
- `cognee>=0.5.0` is wrong. Use `cognee>=1.6.3,<2`.
- "25–45 tests" and "100% offline" aren't rules. What matters is covering the failure modes in §14,
  plus live verification.
- Its sample code has bugs: `def test_source_ sets_cognee_attributes()` won't parse, and its
  incremental template mishandles known ids.
- Tag @NMZivkovic as the official toolkit says. Don't stack mentions or ask for labels repeatedly.
- "Open up to 5 Path B issues" is allowed, but pointless right now: nothing has been accepted since
  Oct 19, and it looks like hoarding.

---

## 17. References

- Rules: https://www.wemakedevs.org/hackathons/mergetober/rules
- Builder's toolkit: https://www.wemakedevs.org/hackathons/mergetober/resources
- Integration guide (a Notion page; it didn't render for the planner, so Vividh should read it in
  a browser): https://app.notion.com/p/topoteretes/Building-a-cognee-Integration-3c937007fa8281b18e83fcc24f86004a
- Connectors repo: https://github.com/topoteretes/cognee-community (CONTRIBUTING.md,
  `.github/pull_request_template.md`, `.github/workflows/ruff.yml`,
  `.github/workflows/onenote_connector_tests.yml`)
- Reference PRs: https://github.com/topoteretes/cognee-community/pull/349 (Asana, merged),
  https://github.com/topoteretes/cognee-community/pull/370 (Google Calendar, merged),
  https://github.com/topoteretes/cognee-community/pull/335 (Evernote, closed)
- Reference issues: https://github.com/topoteretes/cognee/issues/6034 and
  https://github.com/topoteretes/cognee/issues/5972 (accepted Path B proposals)
- Discord: https://discord.gg/NQPKmU5CCg
