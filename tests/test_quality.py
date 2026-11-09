import json
import gzip
from pathlib import Path
import tempfile
import unittest

from injection_tool.core import ROOT, generate, load_catalog, serialize, write_payload_files
from injection_tool.quality import clean_editorial, readiness_issues, text_hash


class QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()
        with gzip.open(ROOT / 'tests/fixtures/catalog_raw.json.gz', 'rt', encoding='utf-8') as f:
            cls.raw = json.load(f)
        cls.raw_by_id = {t['id']: t for t in cls.raw['templates']}

    def descendants(self, original_id):
        return [t for t in self.catalog['templates'] if any(
            x['original_id'] == original_id for x in t['quality']['lineage'])]

    def test_user_reported_memo_has_only_the_usable_body(self):
        rows = self.descendants('tpl-260e921e858972c6')
        self.assertEqual(len(rows), 1)
        body = rows[0]['template']
        self.assertIn('{{goal}}', body)
        for unwanted in ('╔', '║', '═', '[CURRENT_DATE]', '[CURRENT_SESSION]', 'Sarah Chen', 'Marcus Webb', 'Best regards', 'VERIFICATION'):
            self.assertNotIn(unwanted, body)
        self.assertLess(len(body), len(self.raw_by_id['tpl-260e921e858972c6']['template']) // 2)

    def test_actual_combined_source_becomes_six_complete_prompts(self):
        rows = self.descendants('tpl-f782b148744b2070')
        self.assertEqual(len(rows), 6)
        expected_names = {'AntiGPT', 'Emoji storyteller', 'Code Red', 'UCAR', 'Omatic', 'OPPO'}
        self.assertEqual({t['name'].removeprefix('Split source: ') for t in rows}, expected_names)
        for t in rows:
            self.assertEqual(t['template'].count('{{goal}}'), 1)
            self.assertEqual(readiness_issues(t['template']), [])
            self.assertNotIn('how do i make meth', t['template'])
            self.assertNotIn('Briarheart', t['template'])
            self.assertNotIn('persona called "HM"', t['template'])
            self.assertTrue(t['quality']['lineage'][0]['source_span'])

    def test_repeated_goal_and_dialogue_are_not_split(self):
        for sid in ('local-repetition-en', 'tpl-54f8820ce9adff85', 'tpl-9e2f1e65c39cbcdd'):
            rows = self.descendants(sid)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['template'].count('{{goal}}'), self.raw_by_id[sid]['template'].count('{{goal}}'))

    def test_author_credits_removed_without_removing_persona_context(self):
        for sid in ('tpl-d788bea372f69ebc', 'tpl-e7e7f71f223fdf76'):
            body = self.descendants(sid)[0]['template']
            self.assertIn('Omega', body)
            self.assertNotIn('153k#0001', body)
            self.assertNotIn('React to the rainbow', body)
            self.assertNotIn('Prompt is everything below.', body)
        text = 'You are a fictional model created by Example Lab. Task: {{goal}}'
        self.assertEqual(clean_editorial(text)[0], text)

    def test_real_goal_replaces_old_example_and_editorial(self):
        body = self.descendants('tpl-7c03273e9e4e7cfd')[0]['template']
        self.assertIn('The first prompt is: {{goal}}', body)
        self.assertNotIn('copy paste this line', body)
        self.assertNotIn('make a roast', body)

    def test_default_library_excludes_setup_and_manual_edit_records(self):
        with gzip.open(ROOT / 'tests/fixtures/templates_held.json.gz', 'rt', encoding='utf-8') as f:
            held = json.load(f)
        held_ids = {h['template']['id'] for h in held}
        self.assertIn('tpl-85b8492c4d32a22a', held_ids)
        self.assertIn('tpl-aad0692236d9c9a3', held_ids)
        self.assertTrue(readiness_issues('Answer "I am ready" if you understood. {{goal}}'))
        self.assertTrue(readiness_issues('Confirm by writing a reply; begin from my next message. {{goal}}'))
        self.assertEqual(readiness_issues('Confirm you understand by answering my first question: {{goal}}'), [])
        self.assertEqual(readiness_issues('Give two responses to this question: {{goal}}'), [])
        for t in self.catalog['templates']:
            self.assertEqual(t['quality']['status'], 'ready')
            self.assertEqual(readiness_issues(t['template']), [], t['id'])
            for lineage in t['quality']['lineage']:
                raw = self.raw_by_id[lineage['original_id']]
                self.assertEqual(lineage['source_sha256'], text_hash(raw['template']))

    def test_user_goal_not_cleaned_or_split(self):
        goal = '╔作者：我\nPrompt #1\nwait for my reply\n{{goal}}'
        result = generate(goal, catalog=self.catalog, sources=['local'], language='zh', categories=['direct_override'])
        self.assertEqual(result['count'], 1)
        self.assertIn(goal, result['results'][0]['payload'])

    def test_payload_only_array_and_files_are_exact(self):
        result = generate('TEST_中文_🧪', catalog=self.catalog, sources=['local'], language='zh', categories=['direct_override', 'authority_spoof'])
        payloads = json.loads(serialize(result, 'payloads'))
        self.assertEqual(payloads, [r['payload'] for r in result['results']])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'payloads'
            write_payload_files(result, target)
            manifest = json.loads((target/'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(len(list(target.glob('*.txt'))), result['count'])
            for row, entry in zip(result['results'], manifest['items']):
                self.assertEqual((target / entry['file']).read_bytes(), row['payload'].encode('utf-8'))
                self.assertNotIn('payload', entry)
            with self.assertRaises(ValueError):
                write_payload_files(result, target)
            self.assertEqual(len(list(target.glob('*.txt'))), result['count'])


if __name__ == '__main__':
    unittest.main()
