# Contribution drafts (Nov 20, 2026)

Branches are already pushed to your forks. Each section says what you still need to do.

---

## 1. pandas: `str.count` miscounts zero-width and start-anchored patterns (default `str` dtype)

**Branch:** `VividhDesign/pandas:str-count-empty-match` (commit 04766b1)
**Open PR:** https://github.com/pandas-dev/pandas/compare/main...VividhDesign:pandas:str-count-empty-match

pandas' AGENTS.md forbids an agent from opening issues or PRs for you. Its AI policy also requires that the issue and PR text be your own words. So below are facts and code you can quote, not text to paste.

### Steps
1. Open an issue in your own words. You may quote this repro in a code block:
   ```python
   import pandas as pd
   ser = pd.Series(["ab", "東京", "aa"])          # default str dtype (pyarrow)
   ser.str.count("^")     # [3, 7, 3]   expected [1, 1, 1]
   ser.str.count("")      # [3, 7, 3]   expected [3, 3, 3]
   ser.str.count("^a")    # [1, 0, 2]   expected [1, 0, 1]
   pd.Series(["ab", "東京", "aa"], dtype=object).str.count("^")   # [1, 1, 1]
   ```
   Facts for the issue:
   - It's a regression from 2.x, where the default was object dtype with Python `re` semantics.
   - Root cause: `pc.count_substring_regex` re-searches the rest of the string after each match as if it were a new string, so `^`/`\A` match again. After an empty match it also advances one byte rather than one character, so empty matches are counted inside multi-byte characters.
   - It belongs under the regex-engine tracker #63683, whose reproducer script, section G ("zero-width matches in count / replace"), lists these cases. No issue or PR fixes them yet.
2. Replace `XXXXX` in `doc/source/whatsnew/v3.1.2.rst` with the new issue number, then amend and push.
3. Run `/pandas-review` locally until it reports LGTM or NITS ONLY. The policy requires this, and the classifier blocked me from running it.
4. Open the PR. Its body must disclose the tool, model and reasoning setting, as `contributing.rst` requires.

What the change does: `ArrowStringArray._str_count` falls back to Python's `re` when the pattern can match the empty string (min width 0) or contains `^`/`\A`. A new parametrized test, `test_count_zero_width_and_start_anchor`, fails in 18 cases on main and passes with the fix. `pandas/tests/strings` and `pandas/tests/arrays/string_` pass: 6,324 tests on the nightly wheel built from the same commit.

---

## 2. pandas: `str.replace(regex=True)` with zero-width matches and start anchors

**Branch:** `VividhDesign/pandas:str-replace-zero-width` (commit af5b276)
**Open PR:** https://github.com/pandas-dev/pandas/compare/main...VividhDesign:pandas:str-replace-zero-width

The process is the same as #1. It can share the issue: use "xref #N" in one PR and "closes #N" in the other. Repro you can quote:
```python
import pandas as pd
s = pd.Series(["ab", "aa"])
s.str.replace("a?", "-", regex=True)        # ['-b-', '--']   expected ['--b-', '---']
s.str.replace("^", "-", regex=True, n=2)    # ['--ab', '--aa'] expected ['-ab', '-aa']
s.str.replace("^a", "-", regex=True, n=2)   # ['-b', '--']    expected ['-b', '-a']
```
Facts:
- RE2 skips an empty match right after a non-empty one. `re.sub` has replaced those since Python 3.7.
- With `max_replacements`, pyarrow re-searches the rest of the string after each replacement as if it were a new string.
- The fix falls back to Python's `re` only for patterns that can match both empty and non-empty strings, or when `n > 1` and the pattern is zero-width or start-anchored. `str.replace("^", "x", regex=True)` (prefixing) keeps the fast pyarrow path.
- I deliberately left `n=0` out: object dtype itself treats it as "all" with regex but "none" without.

Tests: `test_replace_zero_width_and_start_anchor` has 18 cases that fail on main, and 10,956 string tests pass.

---

## 3. USearch 3.0: NumPy batches of no rows rejected (PR)

**Branch:** `VividhDesign/USearch:fix-empty-dlpack-batches` (commit 39e11c4)
**Open PR:** https://github.com/unum-cloud/USearch/compare/main...VividhDesign:USearch:fix-empty-dlpack-batches

**Before opening:** USearch's `commit-msg` hook, replayed in CI, rejects AI-assistant trailers. Strip them first:
```bash
cd <your usearch clone> && git checkout fix-empty-dlpack-batches && git commit --amend -m "$(git log -1 --format=%B | grep -vE '^(Co-Authored-By: Claude|Claude-Session:)')" && git push -f origin fix-empty-dlpack-batches
```

### PR title
Fix: Accept NumPy batches of no rows through DLPack

### PR description (draft)
NumPy exports a zero-size array through `__dlpack__` with strides `(0, 0)`, which DLPack permits because such a tensor addresses no memory. `buffer_via_dlpack` copied those strides into the `Py_buffer`, so the layout check in `usearch_py_matrix_from_object` read the zero column stride as a gather and refused the batch:

```python
import numpy as np
from usearch import DenseIndex, Arena
index = DenseIndex.init_ram(dimensions=8)
index.insert(np.zeros(0, np.uint64), np.zeros((0, 8), np.float32))
# UnsupportedLayoutError: expected a matrix whose rows are contiguous; only the row stride may vary
index.search(np.zeros((0, 8), np.float32), 3, Arena())   # same error
```

The same batch passed as `memoryview(np.zeros((0, 8), np.float32))` takes the buffer protocol and works. Pipelines that slice batches hit this on their last, empty slice. A tensor of no elements now takes the row-major strides, so both paths agree. Key-count mismatches still raise `ShapeMismatchError`.

Test: `test_batches_of_no_rows_insert_and_answer_nothing` covers NumPy and `memoryview` inputs. It fails before the change and passes after. The Python suite gives 334 passed with a native-only `USEARCH_DENSE_DTYPES=4` build. The one failure, `test_construction_takes_a_pinned_class`, needs the SERIAL class, which that build leaves out.

Question for review: an empty batch of the wrong width, e.g. `(0, 7)` into an 8-dimensional index, is accepted as a no-op, as it already was through the buffer protocol. Happy to make it raise `ShapeMismatchError` instead if you prefer.

(If you used AI help, consider saying so here. The project forbids it in commit trailers, not in PR text.)

---

## 4. USearch issue: one NaN vector corrupts unrelated searches (issue to file)

### Title
Bug: A single NaN row makes unrelated searches miss their own vectors

### Body (draft)
Inserting one vector with NaN components into a dense index makes about 12% of later self-searches for other, finite vectors return the wrong key. Every entry stays reachable (`health().reachable == size`), so the graph isn't disconnected. NaN distances appear to corrupt the ordering of the candidates during traversal. 2.x behaves the same or worse, so it isn't new in 3.0.

```python
import numpy as np
from usearch import DenseIndex, DenseMetric, Arena
rng = np.random.default_rng(42)
X = rng.standard_normal((1000, 16)).astype(np.float32)
index = DenseIndex.init_ram(dimensions=16, metric=DenseMetric.EUCLIDEAN)
index.insert(np.arange(500), X[:500])
index.insert([10_000], np.full((1, 16), np.nan, np.float32))   # one bad row
index.insert(np.arange(500, 1000), X[500:])
m = index.search(X, 1, Arena())
print(sum(int(m[i][0].key) != i for i in range(1000)))   # 120 (0 without the NaN row)
```

| version | without NaN row | with one NaN row |
|---|---|---|
| 3.0.0-rc.1 (`main` 840374a) | 0 / 1000 misses | 120 / 1000 |
| 2.26.6 (`Index`, `l2sq`, `bf16`) | 1 / 1000 | 274 / 1000 |

Embeddings occasionally contain NaN, for example from a divide-by-zero in normalization. One bad row then silently degrades every search instead of failing loudly. Options:
1. Refuse non-finite rows in `insert` with `InvalidArgumentError`, all or nothing like other refusals.
2. Order NaN distances last in the candidate comparisons, so a bad entry is never preferred.

I can send a PR for whichever you prefer.

---

## 5. USearch #815: data showing low connectivity amplifies the same failure (comment)

The issue is https://github.com/unum-cloud/USearch/issues/815. A comment with numbers helps the maintainer's 3.0 graph work. Data for 2,000 Gaussian vectors, 8 dimensions, bf16, Euclidean, self-search `wanted=1`:

| connectivity | 3.0 misses | 3.0 reachable | 3.0 after `refine()` | 2.26.6 misses | hnswlib (M=c) misses |
|---|---|---|---|---|---|
| 2 | 1970 | 14 / 2000 | 1968, reachable 90 | 329 | 343 |
| 4 | 1468 | 1523 / 2000 | 1202, reachable 1972 | 12 | 1 |
| 8 | 24 | 1994 / 2000 | 3, reachable 2000 | 11 | 0 |
| 16 | 0 | 2000 / 2000 | 0 | 15 | 0 |

`init_ram` accepts connectivity 2 and 4, but the graph strands most entries at 2 and about a quarter at 4. Raising the expansion factor to 512 still leaves 500 misses at 4. The mechanism looks like the one in the issue: `back_link_one_` re-selects a full list with `keep_diverse_t`, and nothing guarantees the new node keeps at least one incoming link. If small connectivities aren't meant to be supported, a `ConfigMismatchError` below 8 would be the safer contract.

---

## 6. skpro #1189: pushed the extra test kr1xh suggested

Commit 3ea4400 on `fix-loc-missing-labels` adds the case where `index`/`columns` aren't passed. On main, `ppf(0.5)` returned `[[7.39, 7.39], [54.6, 54.6]]` instead of `exp(mu)`. A short thank-you reply to kr1xh, in your own words, is a good idea.

---
---

# Round 2

## 7. pandas: Python-only regex syntax on the default `str` dtype

**Branch:** `VividhDesign/pandas:str-regex-python-only-syntax` (commit 6265ea1)
**Open PR:** https://github.com/pandas-dev/pandas/compare/main...VividhDesign:pandas:str-regex-python-only-syntax

Repro you can quote:
```python
import pandas as pd
s = pd.Series(["aaab", "b"])
s.str.contains(r"(?>a+)b")   # ArrowInvalid: invalid perl operator: (?>     (object dtype: [True, False])
s.str.contains(r"a++b")      # ArrowInvalid: bad repetition operator: ++
s.str.contains(r"a{,2}b")    # [False, False]   expected [True, True]: Python reads {,2} as {0,2}
```
Facts:
- Atomic groups and possessive quantifiers have been valid Python `re` syntax since Python 3.11, the oldest version pandas supports.
- The fix adds `ATOMIC_GROUP`/`POSSESSIVE_REPEAT` to `unsupported_ops` in `_needs_python_regex`, the same mechanism as lookarounds, plus a source scan for unescaped `{,n}`.
- It updates `test_needs_python_regex_unicode_classes`. That test asserted ASCII data keeps the pyarrow path for `(?>\w)`, but on main that pattern raises `ArrowInvalid` for any data. I moved the case to `test_needs_python_regex_unsupported_code`.
- The new `test_regex_syntax_python_only` has 8 failing cases on main and passes with the fix.
- This is section H plus part of section D of the reproducer script in #63683.

## 8. pandas: escapes in the replacement string

**Branch:** `VividhDesign/pandas:str-replace-repl-escapes` (commit bcff47d)
**Open PR:** https://github.com/pandas-dev/pandas/compare/main...VividhDesign:pandas:str-replace-repl-escapes

```python
import pandas as pd
s = pd.Series(["abc"])
s.str.replace("a", r"\n", regex=True)     # ArrowInvalid: Rewrite schema error   (object dtype: ['\nbc'])
s.str.replace("(a)", r"\0", regex=True)   # ['abc'] (whole match)   expected ['\x00bc'] (octal escape)
```
Facts:
- RE2 rewrite strings take only `\\` and `\1`–`\9`.
- Two-digit references such as `\20` deliberately keep pyarrow's "group 2 then 0" reading, because `test_pyarrow_ambiguous_group_references` (GH#62653) pins it. The fix leaves them alone.
- This is section F of #63683.
- 12 failing cases on main pass with the fix.

### How to open the four pandas PRs
- One issue can cover all four: "regex regressions of the default str dtype not yet covered by #63683 fixes". Reference it in each PR.
- All four add a line at the same spot in `v3.1.2.rst`, so whichever merges second will need a trivial rebase. I merged all four locally and resolved the conflicts:
  - 34,876 string and Arrow tests pass on the combined result.
  - My regex differential scan against object dtype goes from 11 mismatches to 0.
- For each PR: replace `XXXXX`, run `/pandas-review`, and add the AI disclosure.

---

## 9. USearch issue: `values_per_key` is accepted but never enforced by dense indexes

### Title
Bug: Dense indexes accept `values_per_key` but never bound entries per key

### Body (draft)
`usearch_dense_init_ram_t::values_per_key` is documented as the "Upper bound on entries sharing one key; zero is unbounded", but a RAM dense index stores any number of entries under one key:

```python
import numpy as np
from usearch import DenseIndex
X = np.random.default_rng(0).standard_normal((4, 8)).astype(np.float32)
for vpk in (1, 2):
    index = DenseIndex.init_ram(dimensions=8, values_per_key=vpk)
    index.insert([1, 1, 1], X[:3])            # accepted
    index.insert([1], X[3:])                  # accepted
    print(vpk, index.count(1))                # 1 4 / 2 4
```

`usearch_dense_init_ram` and `usearch_dense_init_vram` in `src/dense_index.cuh` never read `arguments->values_per_key`, so the bound is dropped at construction. The basic GPU path refuses a nonzero bound outright ("A GPU index bounds no key's entries"). The dense paths neither honor it nor refuse it. `maxsim` docs present `values_per_key` as the way to declare multi-vector documents, so a caller relying on the bound to cap tokens per document gets silent overflow.

Either enforcing it on `insert`/`absorb` (all-or-nothing, as other refusals are) or refusing a nonzero value until it's implemented would make the contract hold. I can send a PR for whichever you prefer.

---

## 10. USearch issue: float rows into `I8`/`U8` storage silently become zeros

### Title
Docs/Bug: Unit-norm float rows inserted into an `I8` index are stored as all zeros

### Body (draft)
In 3.0, integral storage takes a saturating cast of the input values (as `test/base.py` notes: "Integral storage is a saturating cast, so its rows must already be integers in range"). Feeding it the unit-norm float embeddings that `usearch.eval.random_vectors` produces, described as sitting "in the representable range of every quantization", stores every row as zeros:

```python
import numpy as np
from usearch import DenseIndex, Scalar, Arena
from usearch.eval import random_vectors
X = random_vectors(300, 32)
index = DenseIndex.init_ram(dimensions=32, quantization=Scalar.I8)
index.insert(np.arange(300), X)
print(np.asarray(index.get(0, Arena(), outputs_dtype=Scalar.F32)).ravel()[:4])   # [0. 0. 0. 0.]
m = index.search(X[:50], 1, Arena())
print(sum(int(m[i][0].key) == i for i in range(50)))                             # 4 of 50
```

In 2.x, `Index(dtype="i8")` scaled float input into the int8 range, so 2.x users migrating their float embeddings get a silently useless index. Options: refuse float rows for integral storage unless they're integral; or warn when a row casts to all zeros; or at least document the contract in the `quantization` docs of `init_ram` and the migration notes. Happy to send a docs PR.
