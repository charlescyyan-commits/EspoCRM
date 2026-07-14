from __future__ import annotations

from unittest import TestCase

from chitu_connector.acquisition.master_prospect import (
    RULE_CANONICAL_WEBSITE,
    RULE_COMPANY_CITY,
    RULE_COMPANY_COUNTRY,
    RULE_COMPANY_NAME,
    RULE_ROOT_DOMAIN,
    MasterProspectMerger,
    ProspectMatcher,
    ProspectNormalizer,
    RawProspect,
    normalize_company_name,
)
from chitu_connector.acquisition.models import RawCandidate


MERGE_TIME = "2026-07-13T00:00:00Z"


def raw(
    provider: str,
    candidate_id: str,
    name: str,
    domain: str | None,
    source_url: str | None = None,
    country: str | None = "US",
    *,
    city: str | None = None,
    payload: dict[str, object] | None = None,
) -> RawProspect:
    raw_payload = payload if payload is not None else {"providerRecord": candidate_id}
    return RawProspect(
        provider_name=provider,
        raw_candidate=RawCandidate(candidate_id, name, domain, source_url, country, raw_payload),
        city=city,
        provider_metadata={"fixtureProvider": provider},
        discovery_id="discovery-fixture-001",
    )


class ProspectNormalizationTests(TestCase):
    def test_domain_website_company_and_country_are_canonicalized_without_raw_mutation(self) -> None:
        original_payload = {"nested": {"title": "3D JAKE"}}
        original = raw("APIFY", "a-1", " 3D JAKE ", " HTTPS://www.Example.COM/catalog/ ", "https://www.example.com/about", " us ", payload=original_payload)

        normalized = ProspectNormalizer().normalize(original)

        self.assertEqual(normalized.normalized_domain, "example.com")
        self.assertEqual(normalized.canonical_website, "https://example.com")
        self.assertEqual(normalized.canonical_name, "3djake")
        self.assertEqual(normalized.country, "US")
        self.assertIs(normalized.raw_prospect, original)
        self.assertIs(normalized.raw_prospect.raw_candidate.raw_payload, original_payload)
        self.assertEqual(original.raw_candidate.domain, " HTTPS://www.Example.COM/catalog/ ")

    def test_domain_variants_normalize_to_one_root_domain(self) -> None:
        variants = ("example.com", "www.example.com", "https://example.com", "Example.com")
        values = {
            ProspectNormalizer().normalize(raw("APIFY", str(index), "Example", value)).normalized_domain
            for index, value in enumerate(variants)
        }
        self.assertEqual(values, {"example.com"})

    def test_company_name_normalization_collapses_spacing_case_and_punctuation(self) -> None:
        self.assertEqual({normalize_company_name(value) for value in ("3DJake", "3D JAKE", "3D-Jake")}, {"3djake"})

    def test_company_name_normalization_strips_common_terminal_legal_suffixes(self) -> None:
        variants = ("Example Ltd", "EXAMPLE, INC.", "Example LLC", "Example GmbH", "Example B.V.")
        self.assertEqual({normalize_company_name(value) for value in variants}, {"example"})
        self.assertEqual(normalize_company_name("Ltd"), "ltd")


class ProspectMatchingTests(TestCase):
    def setUp(self) -> None:
        self.normalizer = ProspectNormalizer()
        self.matcher = ProspectMatcher()

    def test_root_domain_has_highest_priority(self) -> None:
        left = self.normalizer.normalize(raw("APIFY", "a", "Different A", "www.example.com", country="US"))
        right = self.normalizer.normalize(raw("SERPER", "b", "Different B", "https://example.com", country="CA"))
        self.assertEqual(self.matcher.match_rule(left, right), RULE_ROOT_DOMAIN)

    def test_source_url_is_canonical_website_fallback_when_domain_is_absent(self) -> None:
        left = self.normalizer.normalize(raw("APIFY", "a", "Different A", None, "https://www.example.com/path"))
        right = self.normalizer.normalize(raw("BRAVE", "b", "Different B", None, "https://example.com/other"))
        self.assertEqual(self.matcher.match_rule(left, right), RULE_CANONICAL_WEBSITE)

    def test_bare_canonical_name_matches_deterministically(self) -> None:
        left = self.normalizer.normalize(raw("APIFY", "a", "3D JAKE", None, None, None))
        right = self.normalizer.normalize(raw("SERPER", "b", "3DJake", None, None, None))
        self.assertEqual(self.matcher.match_rule(left, right), RULE_COMPANY_NAME)

    def test_company_country_and_city_rules_are_exact_and_not_fuzzy(self) -> None:
        country_left = self.normalizer.normalize(raw("APIFY", "a", "3D JAKE", None, None, " us ", city="Austin"))
        country_right = self.normalizer.normalize(raw("SERPER", "b", "3DJake", None, None, "US", city="Dallas"))
        self.assertEqual(self.matcher.match_rule(country_left, country_right), RULE_COMPANY_COUNTRY)

        city_left = self.normalizer.normalize(raw("APIFY", "c", "3D JAKE", None, None, "US", city="Austin"))
        city_right = self.normalizer.normalize(raw("BRAVE", "d", "3DJake", None, None, "CA", city=" austin "))
        self.assertEqual(self.matcher.match_rule(city_left, city_right), RULE_COMPANY_CITY)

        no_match = self.normalizer.normalize(raw("BRAVE", "e", "3DJakes", None, None, "US", city="Austin"))
        self.assertIsNone(self.matcher.match_rule(country_left, no_match))


class MasterProspectMergeTests(TestCase):
    def test_provider_records_merge_to_one_master_with_raw_history_metadata_and_trace(self) -> None:
        apify = raw("APIFY", "apify-1", "3DJake", "Example.COM", "https://example.com", "US", payload={"apify": "original"})
        serper = raw("SERPER", "serper-9", "3D JAKE", "https://www.example.com/", "https://www.example.com/catalog", "US", payload={"serper": "original"})

        result = MasterProspectMerger().merge((apify, serper), merge_timestamp=MERGE_TIME)

        self.assertEqual(len(result.masters), 1)
        master = result.masters[0]
        self.assertTrue(master.master_id.startswith("mp_"))
        self.assertEqual(master.normalized_domain, "example.com")
        self.assertEqual(master.canonical_name, "3djake")
        self.assertEqual(master.website, "https://example.com")
        self.assertEqual(master.source_count, 2)
        self.assertEqual(master.provider_list, ("APIFY", "SERPER"))
        self.assertEqual(master.matched_raw_records, (apify, serper))
        self.assertEqual(master.provider_metadata[0].raw_payload, {"apify": "original"})
        self.assertEqual(master.provider_metadata[1].raw_payload, {"serper": "original"})
        self.assertEqual(len(master.discovery_history), 2)
        self.assertEqual(master.merge_traces[1].matching_rule, RULE_ROOT_DOMAIN)
        self.assertEqual(master.merge_traces[1].confidence, 1.0)
        self.assertEqual(master.merge_traces[1].merge_timestamp, MERGE_TIME)
        self.assertIn("Root domain exact match", master.merge_traces[1].reason)

    def test_duplicate_records_are_merged_but_each_raw_record_is_retained(self) -> None:
        first = raw("APIFY", "same-1", "Example", "example.com", payload={"position": 1})
        duplicate = raw("APIFY", "same-2", "Example", "www.example.com", payload={"position": 2})

        result = MasterProspectMerger().merge((first, duplicate), merge_timestamp=MERGE_TIME)

        self.assertEqual(len(result.masters), 1)
        master = result.masters[0]
        self.assertEqual(master.source_count, 1)
        self.assertEqual(len(master.matched_raw_records), 2)
        self.assertEqual([entry.raw_payload["position"] for entry in master.provider_metadata], [1, 2])
        self.assertEqual(len(result.merge_traces), 2)

    def test_future_provider_merges_without_provider_specific_logic(self) -> None:
        apify = raw("APIFY", "a", "Example", "example.com")
        brave = raw("BRAVE", "b", "Example Corp", "https://www.example.com")

        result = MasterProspectMerger().merge((apify, brave), merge_timestamp=MERGE_TIME)

        self.assertEqual(len(result.masters), 1)
        self.assertEqual(result.masters[0].provider_list, ("APIFY", "BRAVE"))

    def test_unrelated_records_remain_unique_masters(self) -> None:
        first = raw("APIFY", "a", "3DJake", "3djake.example", country="US")
        unrelated = raw("SERPER", "b", "3DJake", "other.example", country="CA")

        result = MasterProspectMerger().merge((first, unrelated), merge_timestamp=MERGE_TIME)

        self.assertEqual(len(result.masters), 2)
        self.assertEqual({master.source_count for master in result.masters}, {1})

    def test_merge_identity_and_trace_are_independent_of_input_order(self) -> None:
        apify = raw("APIFY", "a", "Example", "www.example.com")
        brave = raw("BRAVE", "b", "Example Company", "https://example.com/catalog")

        forward = MasterProspectMerger().merge((apify, brave), merge_timestamp=MERGE_TIME)
        reversed_result = MasterProspectMerger().merge((brave, apify), merge_timestamp=MERGE_TIME)

        self.assertEqual(forward, reversed_result)
