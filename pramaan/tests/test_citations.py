import pytest

from pramaan.citations import extract, find_cites, key_year


@pytest.mark.parametrize(
    "text,key",
    [
        ("(2017) 10 SCC 1", "SCC:2017:10:1"),
        ("(2017) 10 S.C.C. 1", "SCC:2017:10:1"),
        ("2017 (10) SCC 1", "SCC:2017:10:1"),
        ("(1994) Supp (3) SCC 5", "SCC:1994:S3:5"),
        ("1994 Supp (1) SCC 2", "SCC:1994:S1:2"),
        ("(2009) 3 SCC (Cri) 123", "SCC(Cri):2009:3:123"),
        ("(2010) 1 SCC (L&S) 12", "SCC(L&S):2010:1:12"),
        ("(2009) 3 SCC (CRI) 123", "SCC(Cri):2009:3:123"),
        ("(2019) 3 SCC (Civ) 171", "SCC(Civ):2019:3:171"),
        ("1951 SCC 1088", "SCC:1951::1088"),
        ("2020 SCC OnLine SC 341", "SCC_ONLINE:2020:SC:341"),
        ("2023 SCC OnLine Del 1234", "SCC_ONLINE:2023:DEL:1234"),
        ("[2023] 16 S.C.R. 872", "SCR:2023:16:872"),
        ("[1973] Supp. 1 SCR 1", "SCR:1973:S1:1"),
        ("[2004] SUPP. 3 S.C.R. 121", "SCR:2004:S3:121"),
        ("1953 SCR 254", "SCR:1953::254"),
        ("AIR 1973 SC 1461", "AIR:1973:SC:1461"),
        ("A.I.R. 1973 S.C. 1461", "AIR:1973:SC:1461"),
        ("AIR 2005 Bom 123", "AIR:2005:BOM:123"),
        ("2023 INSC 1043", "INSC:2023:1043"),
        ("2023INSC1043", "INSC:2023:1043"),
        ("2023:DHC:1234", "HCN:2023:DHC:1234"),
        ("2024:BHC-AS:12345", "HCN:2024:BHC-AS:12345"),
        ("(2010) 5 SCALE 123", "SCALE:2010:5:123"),
        ("JT 2005 (3) SC 123", "JT:2005:3:123"),
        ("1990 Cri LJ 123", "CRILJ:1990:123"),
        ("MANU/SC/0123/2020", "MANU:SC:123:2020"),
        ("2026 LiveLaw (SC) 653", "LIVELAW:2026:SC:653"),
        ("(2015) 374 ITR 123 (SC)", "ITR:2015:374:123"),
        ("[2015] 59 taxmann.com 123 (SC)", "TAXMANN:2015:59:123"),
    ],
)
def test_reporter_formats(text, key):
    cites = find_cites(f"See {text}, which applies.")
    assert [c.key for c in cites] == [key]


def test_supreme_court_scope():
    sc, hc, air_hc = find_cites("(2017) 10 SCC 1; 2023:DHC:1234; AIR 2005 Bom 123")
    assert sc.is_supreme_court and not hc.is_supreme_court and not air_hc.is_supreme_court


def test_key_year():
    assert key_year("MANU:SC:123:2020") == 2020
    assert key_year("SCC:2017:10:1") == 2017


def test_parallel_citations_and_names():
    t = ("In Kesavananda Bharati v. State of Kerala, (1973) 4 SCC 225 : AIR 1973 SC 1461, at para 316, "
         "the Court said so; see also Maneka Gandhi v. Union of India, (1978) 1 SCC 248.")
    refs = extract(t)
    assert [r.case_name for r in refs] == [
        "Kesavananda Bharati v. State of Kerala",
        "Maneka Gandhi v. Union of India",
    ]
    assert [c.key for c in refs[0].cites] == ["SCC:1973:4:225", "AIR:1973:SC:1461"]
    assert refs[0].pinpoint == "at para 316"


@pytest.mark.parametrize(
    "text,name",
    [
        ("Reliance placed on State Bank of India Vs. M/s Shree Ram Urban Infrastructure Ltd., 2020 SCC OnLine SC 341.",
         "State Bank of India v. M/s Shree Ram Urban Infrastructure Ltd"),
        ("STATE OF PUNJAB V. AJAIB SINGH, 1953 SCR 254", "STATE OF PUNJAB v. AJAIB SINGH"),
        ("Rule in SEBI v. V. Shankar, 2023 INSC 719.", "SEBI v. V. Shankar"),
        ("In re Special Courts Bill, 1978, (1979) 1 SCC 380.", "In re Special Courts Bill, 1978"),
        ("Bar Council of India v. Board of Management, Dayanand College of Law, (2007) 2 SCC 202",
         "Bar Council of India v. Board of Management, Dayanand College of Law"),
        ("Commissioner of Police v. Gordhandas Bhanji [1951 SCC 1088 : AIR 1952 SC 16]",
         "Commissioner of Police v. Gordhandas Bhanji"),
        ("held on 2 May 2019 in Canara Bank v. N.G. Subbaraya Setty & Anr., (2018) 16 SCC 228",
         "Canara Bank v. N.G. Subbaraya Setty & Anr"),
    ],
)
def test_case_names(text, name):
    refs = [r for r in extract(text) if r.cites]
    assert refs[0].case_name == name


def test_name_does_not_cross_paragraphs():
    refs = extract("Ram Kumar v. State of U.P. was argued.\n\n(2017) 10 SCC 1 applies.")
    cited = [r for r in refs if r.cites]
    assert cited[0].case_name is None


def test_uncited_case_names():
    refs = extract("As held in Mercy vs Mankind (2015), compassion matters. The petitioner v. respondent dispute.")
    uncited = [r for r in refs if not r.cites]
    assert [r.case_name for r in uncited] == ["Mercy v. Mankind"]
    assert uncited[0].year_hint == 2015


def test_quotes_attach_to_preceding_authority():
    t = ('In Canara Bank v. N.G. Subbaraya Setty, (2018) 16 SCC 228, the Court held: '
         '"An erroneous decision as to the jurisdiction of a Court cannot clothe that Court with jurisdiction." '
         'Short "quote" is ignored.')
    (ref,) = extract(t)
    assert len(ref.quotes) == 1
    assert ref.quotes[0].text.startswith("An erroneous decision")


def test_no_false_positive_on_plain_numbers():
    assert find_cites("Between 2017 and 2019, 10 people paid Rs 1,000 under Section 11 (2) of the Act.") == []
