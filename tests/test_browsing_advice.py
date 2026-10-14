from unittest import TestCase
from drive_manager.performance import BrowseTiming,browsing_advice
from drive_manager.messages import TEXT

class BrowsingAdviceTests(TestCase):
    def test_measured_combinations_and_threshold(self):
        cases=[((0,0),'browse_fast'),((1.99,1.99),'browse_fast'),((2,1),'browse_listing_slow'),((1,2),'browse_space_slow'),((2,2),'browse_both_slow')]
        for times,key in cases:
            with self.subTest(times=times):self.assertEqual(browsing_advice(BrowseTiming(*times)),key)
    def test_missing_queries_never_report_fast(self):
        for result in [None,BrowseTiming(),BrowseTiming(0,None),BrowseTiming(None,0)]:
            self.assertEqual(browsing_advice(result),'browse_incomplete')
    def test_every_outcome_and_scope_has_four_translations(self):
        for language in ['es','en','fr','de']:
            for key in ['browse_fast','browse_listing_slow','browse_space_slow','browse_both_slow','browse_incomplete','browse_scope']:
                self.assertTrue(TEXT[language][key])
