import base64
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from injection_tool.core import ROOT, CARRIERS, generate, load_catalog, render, serialize, validate_template, wrap


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_all_templates_render_goal(self):
        marker = 'TEST_GOAL_中文_🧪'
        result = generate(marker, catalog=self.catalog)
        self.assertEqual(result['count'], len(self.catalog['templates']))
        for template, row in zip(self.catalog['templates'], result['results']):
            with self.subTest(template=template['id']):
                validate_template(template['template'])
                self.assertNotEqual(row['payload'], template['template'])
                self.assertNotIn('{{goal', row['payload'])
                if '{{goal}}' in template['template']:
                    self.assertIn(marker, row['payload'])

    def test_goal_is_literal_and_one_pass(self):
        goal = '{{goal_base64}} "quoted" {x}\n中文 $() `text`'
        self.assertEqual(render('A{{goal}}B{{goal}}', goal), 'A' + goal + 'B' + goal)

    def test_encoding_roundtrip(self):
        goal = '测试🧪\n"x"'
        self.assertEqual(base64.b64decode(render('{{goal_base64}}', goal)).decode('utf-8'), goal)
        self.assertEqual(json.loads(render('{{goal_json}}', goal)), goal)
        self.assertEqual(''.join(json.loads(render('{{goal_split}}', goal))), goal)
        self.assertEqual(render('{{goal_reversed}}', goal)[::-1], goal)
        self.assertEqual(render('{{goal_unicode}}', goal).encode().decode('unicode_escape'), goal)

    def test_invalid_inputs_fail(self):
        for goal in ('', '   ', None):
            with self.assertRaises(ValueError):
                generate(goal, catalog=self.catalog)
        for kwargs in ({'categories': ['typo']}, {'sources': ['typo']}, {'carriers': ['typo']}, {'language': 'typo'}, {'scope': 'typo'}):
            with self.assertRaises(ValueError):
                generate('test', catalog=self.catalog, **kwargs)
        for template in ('no variable', '{{unknown}}', '{% execute %}{{goal}}'):
            with self.assertRaises(ValueError):
                render(template, 'test')

    def test_filters_and_carriers(self):
        result = generate('marker', catalog=self.catalog, categories=['direct_override'], sources=['local'], language='zh', scope='injection')
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['results'][0]['template_id'], 'local-direct_override-zh')
        matrix = generate('marker', catalog=self.catalog, categories=['direct_override'], sources=['local'], language='zh', carriers=list(CARRIERS))
        self.assertEqual(matrix['count'], len(CARRIERS))
        self.assertEqual(len({r['id'] for r in matrix['results']}), len(CARRIERS))

    def test_structured_carriers_escape(self):
        payload = '"\n,{{goal}}\\中文 <script>alert(1)</script>'
        self.assertEqual(json.loads(wrap(payload, 'tool'))['result'], payload)
        rows = list(csv.reader(io.StringIO(wrap(payload, 'csv'), newline='')))
        self.assertEqual(rows[1][1], payload)

    def test_export_roundtrip(self):
        result = generate('测试\n"目标"', catalog=self.catalog, sources=['local'])
        self.assertEqual(json.loads(serialize(result, 'json')), result)
        lines = [json.loads(line) for line in serialize(result, 'jsonl').splitlines()]
        self.assertEqual(len(lines), result['count'])
        self.assertTrue(all(line['goal'] == result['goal'] for line in lines))

    def test_dedup_and_category_coverage(self):
        ts = self.catalog['templates']
        self.assertEqual(len({t['id'] for t in ts}), len(ts))
        self.assertEqual(len({t['template'].replace('\r\n','\n').strip() for t in ts}), len(ts))
        covered = {c for t in ts for c in t['categories']}
        self.assertEqual(covered, {c['id'] for c in self.catalog['categories']})
        self.assertEqual(dict(Counter(t['scope'] for t in ts)), self.catalog['stats']['templates_by_scope'])

    def test_provenance_and_artifact_integrity(self):
        metadata = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data/source_metadata').glob('*.json')}
        for source in metadata.values():
            for artifact in source['artifacts']:
                file = ROOT/'data/upstream'/source['id']/artifact['path']
                self.assertRegex(artifact['sha256'], r'^[0-9a-f]{64}$')
                self.assertEqual(artifact['url'], f"https://raw.githubusercontent.com/{source['repository']}/{source['commit']}/{artifact['path']}")
                if file.exists():
                    self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), artifact['sha256'])
        for t in self.catalog['templates']:
            for p in t['provenance']:
                if p['source_id'] == 'local':
                    continue
                source = metadata[p['source_id']]
                self.assertEqual(p['commit'], source['commit'])
                self.assertTrue(any(a['path'] == p['path'] for a in source['artifacts']), p)

    def test_cli_multiline_goal_and_error_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            goal = Path(directory)/'goal.txt'
            out = Path(directory)/'result.json'
            goal.write_text('输出标记\nTEST_🧪', encoding='utf-8-sig')
            p = subprocess.run([sys.executable, str(ROOT/'app.py'), 'generate', '--goal-file', str(goal), '--source', 'local', '--out', str(out)], capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['goal'], '输出标记\nTEST_🧪')
        p = subprocess.run([sys.executable, str(ROOT/'app.py'), 'generate', '--goal', 'test', '--category', 'does-not-exist'], capture_output=True)
        self.assertEqual(p.returncode, 2)

    def test_compressed_examples_cli(self):
        p = subprocess.run([sys.executable, str(ROOT/'app.py'), 'examples', '--source', 'ccbos', '--limit', '1'], capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        row = json.loads(p.stdout.decode('utf-8'))
        self.assertTrue(any(item['source_id'] == 'ccbos' for item in row['provenance']))

if __name__ == '__main__':
    unittest.main()
