import unittest
from drive_manager.oauth_output import OAuthOutput

class OAuthOutputTests(unittest.TestCase):
    def test_real_rclone_128_bit_state_has_22_characters(self):
        urls = []; output = OAuthOutput(urls.append)
        url = 'http://127.0.0.1:53682/auth?state=' + 'a' * 22
        output.feed(('NOTICE: Please go to the following link: ' + url + '\n').encode())
        self.assertEqual(urls, [url])

    def test_fragmented_link_forwarded_once(self):
        urls = []; output = OAuthOutput(urls.append)
        url = 'http://127.0.0.1:53682/auth?state=' + 'a' * 128
        line = ('NOTICE: Please go to the following link: ' + url + '\n').encode()
        output.feed(line[:30]); output.feed(line[30:]); output.feed(line)
        self.assertEqual(urls, [url])
    def test_tokens_and_untrusted_links_not_forwarded(self):
        urls = []; output = OAuthOutput(urls.append)
        output.feed(b'Access token=SECRET\nhttp://example.com/auth?state=abc\n')
        output.feed(('http://127.0.0.1:1234/auth?state=' + 'a'*128 + '\n').encode())
        self.assertEqual(urls, [])
        self.assertEqual(output.pending, b'')
    def test_port_conflict_translated_without_raw_diagnostic(self):
        output = OAuthOutput()
        output.feed(b'ERROR: failed to start auth webserver: bind: address already in use SECRET\n')
        self.assertEqual(output.error_key, 'oauth_port')
        self.assertNotIn('SECRET', repr(output.__dict__))
    def test_buffer_bounded(self):
        output = OAuthOutput()
        output.feed(b'x' * 16000)
        self.assertLessEqual(len(output.pending), 8192)
