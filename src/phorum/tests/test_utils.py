from django.test import SimpleTestCase

from ..utils import parse_search_query, build_token_pattern, build_search_patterns, SearchToken


class UtilsTest(SimpleTestCase):
    def test_parse_search_query(self):
        # Single words - returns SearchToken namedtuples
        self.assertEqual(parse_search_query('cat'), [SearchToken('cat', False)])
        self.assertEqual(
            parse_search_query('cat dog'),
            [SearchToken('cat', False), SearchToken('dog', False)]
        )
        self.assertEqual(
            parse_search_query('cat chases dog'),
            [SearchToken('cat', False), SearchToken('chases', False), SearchToken('dog', False)]
        )

        # Quoted phrases
        self.assertEqual(parse_search_query('"cat chases"'), [SearchToken('cat chases', True)])
        self.assertEqual(
            parse_search_query('"cat chases" dog'),
            [SearchToken('cat chases', True), SearchToken('dog', False)]
        )
        self.assertEqual(
            parse_search_query('a "b c" d'),
            [SearchToken('a', False), SearchToken('b c', True), SearchToken('d', False)]
        )

        # Mixed with wildcards (wildcards stay in tokens)
        self.assertEqual(
            parse_search_query('cat* dog'),
            [SearchToken('cat*', False), SearchToken('dog', False)]
        )
        self.assertEqual(
            parse_search_query('"cat*" dog'),
            [SearchToken('cat*', True), SearchToken('dog', False)]
        )

    def test_build_token_pattern(self):
        # No wildcard: word boundaries on both sides
        self.assertEqual(build_token_pattern('word'), r'\yword\y')
        self.assertEqual(build_token_pattern('hello world'), r'\yhello\ world\y')

        # Start wildcard: no start boundary, \S* for non-whitespace
        self.assertEqual(build_token_pattern('*word'), r'\S*word\y')
        self.assertEqual(build_token_pattern('*koko'), r'\S*koko\y')

        # End wildcard: no end boundary
        self.assertEqual(build_token_pattern('word*'), r'\yword\S*')
        self.assertEqual(build_token_pattern('koko*'), r'\ykoko\S*')

        # Both wildcards: no boundaries
        self.assertEqual(build_token_pattern('*word*'), r'\S*word\S*')
        self.assertEqual(build_token_pattern('*middle*'), r'\S*middle\S*')

        # Internal wildcard: boundaries on edges
        self.assertEqual(build_token_pattern('wo*rd'), r'\ywo\S*rd\y')
        self.assertEqual(build_token_pattern('hel*lo'), r'\yhel\S*lo\y')

        # Phrases: wildcards are literal
        self.assertEqual(build_token_pattern('cat*', is_phrase=True), r'\ycat\*\y')
        self.assertEqual(build_token_pattern('*cat', is_phrase=True), r'\y\*cat\y')
        self.assertEqual(build_token_pattern('cat chases', is_phrase=True), r'\ycat\ chases\y')

    def test_build_search_patterns(self):
        # Single token
        self.assertEqual(build_search_patterns('cat'), [r'\ycat\y'])

        # Multiple tokens (word order independent)
        self.assertEqual(build_search_patterns('cat dog'), [r'\ycat\y', r'\ydog\y'])

        # Quoted phrase stays together
        self.assertEqual(
            build_search_patterns('"cat chases" dog'),
            [r'\ycat\ chases\y', r'\ydog\y']
        )

        # Wildcards in words
        self.assertEqual(
            build_search_patterns('koko* *test'),
            [r'\ykoko\S*', r'\S*test\y']
        )

        # Wildcards in phrases are literal
        self.assertEqual(
            build_search_patterns('"cat*" dog*'),
            [r'\ycat\*\y', r'\ydog\S*']
        )
