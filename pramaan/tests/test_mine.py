from pramaan.corpus import Corpus, build_db
from pramaan.mine import clean_judgment_text, mine

RECORDS = [
    dict(title="CANARA BANK versus N. G. SUBBARAYA SETTY & ANR.", petitioner="CANARA BANK",
         respondent="N. G. SUBBARAYA SETTY & ANR.", decision_date="20-04-2018", path="2018_3_884_926",
         nc_display="2018INSC385", year="2018"),
]

CITING = """The principle is settled. See Canara Bank v. N.G. Subbaraya Setty, (2018) 16 SCC 228 : [2018] 3 SCR 884,
and M. Subramaniam v. S. Janaki, (2020) 16 SCC 728."""

CONDEMNING = """It is not in dispute that the judgments relied upon by the NCLT are non-existent.
ICICI Bank Ltd. v. Urban Infrastructure Real Estate Ltd., (2019) 16 SCC 528 - Nonexistent citation."""


def test_attestations_and_parallel_resolution(tmp_path):
    db = tmp_path / "sc.sqlite"
    build_db(RECORDS, db)
    rows = mine([("a", CITING), ("b", CITING)], Corpus(db))
    by_key = {r[0]: r for r in rows}
    # The SCC citation is tied to the official record through its SCR parallel.
    assert by_key["SCC:2018:16:228"][4] is not None and by_key["SCC:2018:16:228"][5] == "parallel"
    assert by_key["SCC:2018:16:228"][3] == 2  # cited in two judgments
    # A case outside the SCR corpus is still attested by name.
    assert by_key["SCC:2020:16:728"][1:3] == ("M. Subramaniam", "S. Janaki")


def test_judgment_discussing_fake_citations_is_not_an_attestation(tmp_path):
    db = tmp_path / "sc.sqlite"
    build_db(RECORDS, db)
    rows = mine([("c", CONDEMNING)], Corpus(db))
    assert not [r for r in rows if r[0] == "SCC:2019:16:528"]


def test_judgment_about_fakes_quoting_them_far_from_the_condemnation(tmp_path):
    db = tmp_path / "sc.sqlite"
    build_db(RECORDS, db)
    filler = "The appellant made submissions on merits. " * 60
    text = ("The Tribunal relied on Sarbjit Singh v. Union Bank of India, (2022) 7 SCC 464. " + filler +
            "These are AI-generated, non-existent judgments. Reliance on fake judgments is misconduct.")
    assert mine([("d", text)], Corpus(db)) == []


def test_clean_judgment_text_strips_scr_furniture():
    raw = ("726            SUPREME COURT REPORTS                     [2023] 10 S.C.R.\n"
           "D           Millikarjun Bhavanappa Tirumale AIR 1960 SC 137 :\n"
           "the appellant contended that the trans-\nfer was void.        E\n")
    t = clean_judgment_text(raw)
    assert "SUPREME COURT REPORTS" not in t
    assert t.splitlines()[1].strip().startswith("Millikarjun")
    assert "transfer was void." in t
