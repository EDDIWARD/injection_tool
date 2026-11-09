import ast
import json
from pathlib import Path
import sys
import unittest

from injection_tool.core import ROOT, generate, load_catalog, render
from injection_tool.quality import clean_editorial
sys.path.insert(0, str(ROOT / 'scripts'))
from expanded_adapters import extract_simple_fstring, factor_exact_goals


class ExpansionTests(unittest.TestCase):
    def test_exact_goal_factoring_rejects_ambiguous_or_absent_goals(self):
        rows = [{'query': 'A: ONE'}, {'query': 'A: TWO'}, {'query': 'ONE TWO'}, {'query': 'none'}]
        self.assertEqual(factor_exact_goals(rows, ['ONE', 'TWO']), {'A: {{goal}}': [0, 1]})

    def test_fstring_extractor_rejects_executable_expressions(self):
        self.assertEqual(extract_simple_fstring(ast.parse("f'Hello {attack}'", mode='eval').body, 'attack'), 'Hello {{goal}}')
        for code in ("f'{attack.upper()}'", "f'{attack!r}'", "f'{other}'", "f'{attack:>20}'"):
            self.assertIsNone(extract_simple_fstring(ast.parse(code, mode='eval').body, 'attack'))

    def test_code_goal_roundtrip_without_execution(self):
        goal = '中文🧪\n"quoted"\\ {x} $()'
        for field in ('goal_code_list', 'goal_code_stack'):
            text = render('{{' + field + '}}', goal)
            tree = ast.parse('def sample():\n' + text)
            chars = [node.value.args[0].value for node in tree.body[0].body]
            if field == 'goal_code_stack':
                chars.reverse()
            self.assertEqual(''.join(chars), goal)
        self.assertEqual(render('{{goal_word_reversed}}', 'one two three'), 'three two one')
        self.assertEqual(render('{{goal_chars_in_words}}', 'one two 中文'), 'eno owt 文中')

    def test_new_sources_and_classical_chinese_are_distinguished(self):
        cat = load_catalog()
        for sid in ('aiinfra', 'easyjailbreak', 'arth_templates', 'jailbench', 'codeattack', 'renellm', 'flipattack', 'libertas', 'piarena'):
            result = generate('输出 TEST_OK', catalog=cat, sources=[sid])
            self.assertGreater(result['count'], 0, sid)
        classical = generate('输出 TEST_OK', catalog=cat, categories=['classical_chinese'])
        self.assertEqual(classical['count'], 4)
        for row in classical['results']:
            self.assertIn('输出 TEST_OK', row['payload'])
            self.assertTrue(all(p['source_id'] == 'local' for p in row['provenance']))
        ccbos = next(s for s in cat['sources'] if s['id'] == 'ccbos')
        self.assertEqual(ccbos['template_count'], 0)
        self.assertGreater(ccbos['example_count'], 0)

    def test_no_bundled_pages_or_author_watermark_in_reviewed_import(self):
        rows = generate('TEST_OK', sources=['libertas'])['results']
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertNotIn('PLINY', row['payload'])
            self.assertNotIn('{Z}', row['payload'])
            self.assertNotIn('{user_input', row['payload'])
            self.assertIn('TEST_OK', row['payload'])

    def test_added_decorations_and_unfilled_dates_are_removed(self):
        clean, _, _ = clean_editorial('∞∞∞∞\n∞ TITLE ∞\nAuthorization Date: [CURRENT_DATE - 7 days]\nDATE: [CURRENT DATE]\n{{goal}}')
        self.assertEqual(clean, 'TITLE\n\n{{goal}}')


if __name__ == '__main__':
    unittest.main()
