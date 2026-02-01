from django.test import SimpleTestCase

from voice.parser import normalize, rules_parse, INTENT_BUDGET_PLAN, INTENT_PRODUCT_SEARCH


class VoiceParserTests(SimpleTestCase):
    def test_product_search_with_max_price(self):
        text = "find catfish under £20"
        parsed = rules_parse(normalize(text))
        self.assertEqual(parsed["intent"], INTENT_PRODUCT_SEARCH)
        self.assertIn("catfish", parsed["entities"]["items"])
        self.assertEqual(parsed["entities"]["max_price"], 20.0)

    def test_budget_plan_with_items(self):
        text = "I have 20 pounds for rice and fish"
        parsed = rules_parse(normalize(text))
        self.assertEqual(parsed["intent"], INTENT_BUDGET_PLAN)
        self.assertEqual(parsed["entities"]["amount"], 20.0)
        self.assertIn("rice", parsed["entities"]["items"])
        self.assertIn("fish", parsed["entities"]["items"])
