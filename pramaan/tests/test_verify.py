"""End-to-end verdicts against a small, hand-built index."""

from pathlib import Path

import pytest

from pramaan.corpus import Corpus, build_db
from pramaan.mine import save
from pramaan.names import NameIndex, tokens
from pramaan.quotes import TextSource, match_quote
from pramaan.verify import Verifier, check_text

RECORDS = [
    dict(title="CANARA BANK versus N. G. SUBBARAYA SETTY & ANR.", petitioner="CANARA BANK",
         respondent="N. G. SUBBARAYA SETTY & ANR.", decision_date="20-04-2018", path="2018_3_884_926",
         nc_display="2018INSC385", year="2018", judge="R.F. NARIMAN"),
    dict(title="HIS HOLINESS KESAVANANDA BHARATI SRIPADAGALAVARU versus STATE OF KERALA",
         petitioner="HIS HOLINESS KESAVANANDA BHARATI SRIPADAGALAVARU", respondent="STATE OF KERALA",
         decision_date="24-04-1973", path="S_1973_1_1_1002", nc_display="1973INSC91", year="1973"),
    dict(title="COMMISSIONER OF INCOME-TAX, MADRAS versus S. RAMAN CHETTIAR",
         petitioner="COMMISSIONER OF INCOME-TAX, MADRAS", respondent="S. RAMAN CHETTIAR",
         decision_date="27-10-1964", path="1965_1_883_889", nc_display="1964INSC234", year="1965"),
    dict(title="MANEKA GANDHI versus UNION OF INDIA", petitioner="MANEKA GANDHI", respondent="UNION OF INDIA",
         decision_date="25-01-1978", path="1978_2_621_776", nc_display="1978INSC16", year="1978"),
    dict(title="SECURITIES AND EXCHANGE BOARD OF INDIA versus V SHANKAR",
         petitioner="SECURITIES AND EXCHANGE BOARD OF INDIA", respondent="V SHANKAR",
         decision_date="08-02-2023", path="2023_6_419_424", nc_display="2023INSC719", year="2023"),
    # Keeps the index's coverage running to 2026, as the real one does.
    dict(title="POOJA RAMESH SINGH versus JAMMU AND KASHMIR BANK LTD. & ANR.", petitioner="POOJA RAMESH SINGH",
         respondent="JAMMU AND KASHMIR BANK LTD. & ANR.", decision_date="02-07-2026", path="2026_7_1_11",
         nc_display="2026INSC668", year="2026"),
]

CANARA_TEXT = """CANARA BANK v. N. G. SUBBARAYA SETTY
An erroneous decision as to the jurisdiction of a Court cannot clothe that
Court with jurisdiction where it has none. Obviously, a Civil Court cannot send
a person to jail for an offence committed under the Penal Code."""


@pytest.fixture(scope="module")
def verifier(tmp_path_factory) -> Verifier:
    root: Path = tmp_path_factory.mktemp("idx")
    db = root / "sc.sqlite"
    build_db(RECORDS, db)
    c = Corpus(db)
    ids = {j.path: j.id for j in c.docs.values()}
    save([
        ("SCC:2018:16:228", "Canara Bank", "N.G. Subbaraya Setty", 7, ids["2018_3_884_926"], "parallel"),
        ("SCC:1973:4:225", "Kesavananda Bharati", "State of Kerala", 120, ids["S_1973_1_1_1002"], "parallel"),
        ("SCC:1978:1:248", "Maneka Gandhi", "Union of India", 90, ids["1978_2_621_776"], "parallel"),
        # A case that is not in the SCR corpus, known only from how later judgments cite it.
        ("SCC:2020:16:728", "M. Subramaniam", "S. Janaki", 3, None, None),
        ("SCC_ONLINE:2020:SC:341", "M. Subramaniam", "S. Janaki", 3, None, None),
    ], db)
    texts = root / "texts" / "2018"
    texts.mkdir(parents=True)
    (texts / "2018_3_884_926_EN.txt").write_text(CANARA_TEXT)
    return Verifier(Corpus(db), TextSource(text_dir=root / "texts", allow_network=False))


def one(verifier, text):
    findings = check_text(text, verifier)
    assert len(findings) == 1, [f.ref.label for f in findings]
    return findings[0]


def test_verified_by_official_scr_record(verifier):
    f = one(verifier, "Kesavananda Bharati v. State of Kerala, [1973] Supp. 1 SCR 1.")
    assert (f.status, f.risk) == ("VERIFIED", "ok")


def test_verified_by_attestation(verifier):
    f = one(verifier, "Canara Bank v. N.G. Subbaraya Setty & Anr., (2018) 16 SCC 228.")
    assert f.status == "VERIFIED"


def test_verified_for_case_outside_scr_corpus(verifier):
    f = one(verifier, "M. Subramaniam v. S. Janaki, (2020) 16 SCC 728.")
    assert f.status == "VERIFIED"


def test_citation_of_a_different_case(verifier):
    # The NCLT's error: a real SCC OnLine number that belongs to another case.
    f = one(verifier, "State Bank of India v. M/s Shree Ram Urban Infrastructure Ltd., 2020 SCC OnLine SC 341.")
    assert (f.status, f.risk) == ("WRONG_CITATION", "high")
    assert "Subramaniam" in f.message


def test_real_case_wrong_reporter_page(verifier):
    f = one(verifier, "Maneka Gandhi v. Union of India, (1978) 2 SCC 999.")
    assert f.status == "WRONG_CITATION"
    assert "(1978) 1 SCC 248" in f.message


def test_neutral_citation_pointing_elsewhere(verifier):
    f = one(verifier, "Maneka Gandhi v. Union of India, 2023 INSC 719.")
    assert (f.status, f.risk) == ("WRONG_CITATION", "high")


def test_year_mismatch(verifier):
    f = one(verifier, "Canara Bank v. N.G. Subbaraya Setty, (2009) 3 SCC 100.")
    assert (f.status, f.risk) == ("YEAR_MISMATCH", "high")


def test_year_mismatch_with_a_government_party_is_only_review(verifier):
    # Revenue and State parties appear in many cases; another year may be another case.
    f = one(verifier, "CIT v. Raman Chettiar, (1972) 2 SCC 100.")
    assert (f.status, f.risk) == ("YEAR_MISMATCH", "review")


def test_case_found_without_reporter_confirmation(verifier):
    f = one(verifier, "CIT v. S. Raman Chettiar, (1965) 1 SCC 50.")
    assert (f.status, f.risk) == ("CASE_FOUND", "ok")


def test_fabricated_case(verifier):
    f = one(verifier, "Sarbjit Singh v. Union Bank of India, (2022) 7 SCC 464.")
    assert (f.status, f.risk) == ("NOT_FOUND", "high")


def test_nonexistent_neutral_number(verifier):
    f = one(verifier, "See 2023 INSC 99999.")
    assert (f.status, f.risk) == ("NOT_FOUND", "high")


def test_recent_online_citation_is_review_not_high(verifier):
    # SCC OnLine also reports unreported orders, so a miss is weaker evidence.
    f = one(verifier, "Ramesh Kumar Jha v. Bihar Khadi Gramodyog Sangh, 2025 SCC OnLine SC 1234.")
    assert (f.status, f.risk) == ("NOT_FOUND", "review")


def test_same_case_with_respondent_named_differently(verifier):
    f = one(verifier, "SEBI v. V. Shankar & Ors., 2023 INSC 719.")
    assert f.risk == "ok"
    f = one(verifier, "Securities and Exchange Board of India v. State of Gujarat, 2023 INSC 719.")
    assert f.risk == "review"


def test_uncited_name_is_review_not_high(verifier):
    f = one(verifier, "As held in Mercy vs Mankind (2015), compassion matters.")
    assert (f.status, f.risk) == ("UNVERIFIED", "review")


def test_supreme_court_citation_before_1950_is_impossible(verifier):
    f = one(verifier, "Ram v. Shyam, AIR 1944 SC 73.")
    assert (f.status, f.risk) == ("NOT_FOUND", "high")


def test_high_court_citation_is_out_of_scope(verifier):
    f = one(verifier, "The Delhi High Court agreed in 2023:DHC:1234.")
    assert f.status == "OUT_OF_SCOPE"


def test_real_quote_is_found(verifier):
    f = one(verifier, 'Canara Bank v. N.G. Subbaraya Setty, (2018) 16 SCC 228 held that "An erroneous decision as '
                      'to the jurisdiction of a Court cannot clothe that Court with jurisdiction where it has none."')
    assert f.status == "VERIFIED"
    assert f.quotes[0].status == "FOUND"


def test_fabricated_quote_in_real_case(verifier):
    f = one(verifier, 'In Canara Bank v. N.G. Subbaraya Setty, (2018) 16 SCC 228, the Court held: "A corporate '
                      'guarantee survives the demerger or amalgamation of the guarantor company and is not '
                      'extinguished by internal restructuring."')
    assert (f.status, f.risk) == ("QUOTE_NOT_FOUND", "high")


def test_quote_matching_tolerates_layout_noise():
    judgment = "the rule of law\nis the basic struc-\nture of the Constitution and cannot be abrogated"
    r = match_quote("the rule of law is the basic structure of the Constitution and cannot be abrogated", judgment)
    assert r.status == "FOUND"
    r = match_quote("the rule of law is a flexible doctrine that Parliament may amend at will", judgment)
    assert r.status == "NOT_FOUND"


def test_name_normalisation():
    assert tokens("U.O.I.") == ["UNION", "INDIA"]
    assert tokens("CIT, Madras") == tokens("Commissioner of Income Tax, Madras")
    idx = NameIndex()
    idx.add(1, "HIS HOLINESS KESAVANANDA BHARATI", "STATE OF KERALA")
    idx.add(2, "STATE OF KERALA", "RAM KUMAR")
    assert idx.search("Keshavananda Bharti", "State of Kerala")[0][0] == 1
