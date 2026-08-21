"""
Run with: python3 -m unittest py.test_sync_partner_feed -v
Uses the stdlib unittest module only (no new dependency).
"""
import unittest

from sync_partner_feed import sanitize_feed, ALLOWED_LINK_HOSTS


def make_camp(name="Test Camp", link="https://www.outdoorcampingworld.com/camp/test", **overrides):
    camp = {"name": name, "link": link}
    camp.update(overrides)
    return camp


class SanitizeFeedTopLevelTests(unittest.TestCase):
    def test_rejects_non_dict_top_level(self):
        for bad in ([], "a string", 123, None, True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    sanitize_feed(bad)

    def test_accepts_empty_dict(self):
        clean, stats = sanitize_feed({})
        self.assertEqual(clean, {})
        self.assertEqual(stats["cities"], 0)

    def test_skips_non_list_city_value(self):
        clean, stats = sanitize_feed({"苗栗縣": "not a list"})
        self.assertEqual(clean, {})


class SanitizeFeedLinkValidationTests(unittest.TestCase):
    def test_accepts_legit_camp(self):
        data = {"苗栗縣": [make_camp()]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(stats["campaigns_accepted"], 1)
        self.assertEqual(stats["campaigns_rejected"], 0)
        self.assertIn("苗栗縣", clean)

    def test_rejects_javascript_uri(self):
        data = {"苗栗縣": [make_camp(link="javascript:alert(1)")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})
        self.assertEqual(stats["campaigns_rejected"], 1)

    def test_rejects_javascript_uri_mixed_case(self):
        data = {"苗栗縣": [make_camp(link="JaVaScRiPt:alert(1)")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})

    def test_rejects_data_uri(self):
        data = {"苗栗縣": [make_camp(link="data:text/html,<script>alert(1)</script>")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})

    def test_rejects_protocol_relative(self):
        data = {"苗栗縣": [make_camp(link="//evil.example/x")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})

    def test_rejects_http_not_https(self):
        data = {"苗栗縣": [make_camp(link="http://www.outdoorcampingworld.com/x")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})

    def test_rejects_lookalike_host(self):
        data = {"苗栗縣": [make_camp(link="https://www.outdoorcampingworld.com.evil.test/x")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})

    def test_rejects_userinfo_bypass(self):
        data = {
            "苗栗縣": [make_camp(link="https://www.outdoorcampingworld.com@evil.test/x")]
        }
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})

    def test_rejects_missing_required_fields(self):
        data = {"苗栗縣": [{"name": "No Link Camp"}]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean, {})
        self.assertEqual(stats["campaigns_rejected"], 1)

    def test_one_bad_campaign_does_not_drop_good_ones_in_same_city(self):
        data = {
            "苗栗縣": [
                make_camp(name="Good Camp"),
                make_camp(name="Bad Camp", link="javascript:alert(1)"),
            ]
        }
        clean, stats = sanitize_feed(data)
        self.assertEqual(len(clean["苗栗縣"]), 1)
        self.assertEqual(clean["苗栗縣"][0]["name"], "Good Camp")
        self.assertEqual(stats["campaigns_accepted"], 1)
        self.assertEqual(stats["campaigns_rejected"], 1)

    def test_bad_campaign_in_one_city_does_not_affect_other_cities(self):
        data = {
            "苗栗縣": [make_camp(link="javascript:alert(1)")],
            "南投縣": [make_camp(name="Good Camp")],
        }
        clean, stats = sanitize_feed(data)
        self.assertNotIn("苗栗縣", clean)
        self.assertIn("南投縣", clean)
        self.assertEqual(len(clean["南投縣"]), 1)

    def test_output_schema_shape_preserved(self):
        data = {"苗栗縣": [make_camp()]}
        clean, _ = sanitize_feed(data)
        self.assertIsInstance(clean, dict)
        self.assertIsInstance(clean["苗栗縣"], list)
        self.assertIsInstance(clean["苗栗縣"][0], dict)


class SanitizeFeedImageValidationTests(unittest.TestCase):
    def test_safe_internal_image_path_kept(self):
        data = {"苗栗縣": [make_camp(image="/images/camps/default.webp")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean["苗栗縣"][0]["image"], "/images/camps/default.webp")
        self.assertEqual(stats["images_replaced"], 0)

    def test_external_image_replaced_with_default(self):
        data = {"苗栗縣": [make_camp(image="https://evil.example/tracker.gif")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean["苗栗縣"][0]["image"], "/images/camps/default.webp")
        self.assertEqual(stats["images_replaced"], 1)

    def test_javascript_uri_image_replaced_not_dropped(self):
        data = {"苗栗縣": [make_camp(image="javascript:alert(1)")]}
        clean, stats = sanitize_feed(data)
        # The campaign itself is still accepted (link was valid); only the
        # dangerous image field is neutralized, not the whole campaign.
        self.assertEqual(len(clean["苗栗縣"]), 1)
        self.assertEqual(clean["苗栗縣"][0]["image"], "/images/camps/default.webp")

    def test_protocol_relative_image_replaced(self):
        data = {"苗栗縣": [make_camp(image="//evil.example/x.jpg")]}
        clean, stats = sanitize_feed(data)
        self.assertEqual(clean["苗栗縣"][0]["image"], "/images/camps/default.webp")


class AllowedLinkHostsConstantTests(unittest.TestCase):
    def test_known_partner_host_present(self):
        self.assertIn("www.outdoorcampingworld.com", ALLOWED_LINK_HOSTS)


if __name__ == "__main__":
    unittest.main()
