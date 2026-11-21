### Hi, I'm Vividh 👋

Final-year B.Tech in AI & ML at BIT Mesra (graduating May 2027). I fix bugs in widely used open-source ML and database libraries, and I build retrieval and vector-search systems from scratch.

**Open to** SWE, ML engineering and AI-evaluation roles (full-time or contract) · 📫 vividh2004@gmail.com · [LinkedIn](https://linkedin.com/in/vividh-yadav-866a44380/)

#### 🌱 Merged open-source work (reviewed by each project's maintainers)

| Project | What I fixed | PR |
|---|---|---|
| **pandas** (50K★) | Regression test for `groupby(...).rolling()` keeping group order with `sort=False` (closes GH 50296) | [#71327](https://github.com/pandas-dev/pandas/pull/71327) |
| **sktime** (10K★) | Multivariate forecast quantiles were filed under the wrong variables (VAR, VECM, DynamicFactor) | [#11424](https://github.com/sktime/sktime/pull/11424) |
| **sktime** | Median metrics crashed with a list or tuple `horizon_weight` | [#11370](https://github.com/sktime/sktime/pull/11370) |
| **skpro** | The same quantile mix-up, for multi-output probabilistic regression | [#1211](https://github.com/sktime/skpro/pull/1211) |
| **skbase** | `all_objects` tag filter crashed on unhashable tag values | [#603](https://github.com/sktime/skbase/pull/603) |
| **USearch** (4K★) | After `compact()`, 1,975 of 2,000 keys returned the wrong vector. Merged by the creator the same day. | [#793](https://github.com/unum-cloud/USearch/pull/793) |

In review: MariaDB [#5879](https://github.com/MariaDB/server/pull/5879) (vector-index crash, approved in preliminary review) · Django [#22175](https://github.com/django/django/pull/22175) · sktime [#11453](https://github.com/sktime/sktime/pull/11453)

#### 🛠️ Things I built

- **[Pramaan](https://github.com/VividhDesign/pramaan)** · [try it](https://vividhdesign.github.io/pramaan/): catches fake case citations in Indian legal filings, the problem behind the Supreme Court's 2026 "zero tolerance" ruling (2026 INSC 668). It checks every citation against 38k Supreme Court judgments and an open concordance of 45k citations mined from 94k Supreme Court and High Court judgments. It flags invented cases, misattributed citations and quotes that aren't in the judgment. On a held-out test: 1.2% false alarms; 97.7–99.9% of each kind of fabrication flagged. Runs in the browser; documents are never uploaded.
- **[Strata](https://github.com/VividhDesign/strata)**: a vector database from scratch in C++17 (HNSW, NEON/AVX2 SIMD, WAL, REST server, Python bindings). On SIFT1M it matches FAISS and runs 1.9× faster than hnswlib at equal recall.
- **[Evident](https://github.com/VividhDesign/evident)** · [live demo](https://evident-rag.streamlit.app): RAG where every component is measured. Its BM25 reproduces Pyserini within ±0.002; LLM-as-judge harness with bootstrap CIs.
- **[Dhuaan](https://github.com/VividhDesign/dhuaan)** · [live](https://main.d300fn6sn0z3go.amplifyapp.com): forecasts when farm-fire smoke will reach your area and alerts you in Hindi or English. Runner-up, WeMakeDevs × AWS.
- **[Kavach](https://github.com/VividhDesign/kavach)**: worker-safety monitoring on CCTV feeds: danger zones, man-down detection, PPE checks (OpenCV, YOLO11).
- **[OverlayAi](https://github.com/VividhDesign/OverlayAi)**: an always-on-top AI assistant for macOS (Electron; Ollama, Gemini, Groq). DMG on Releases.

#### 📄 Research

*A transformer-based architecture for pre-impact fall detection with highly imbalanced data*: accepted at the 14th IEEE ISED 2026 (co-author).

LeetCode Knight, max rating 2001.
