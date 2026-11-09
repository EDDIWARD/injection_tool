"""Reproducible, content-addressed manual decisions for the original import.

Segments below were inspected as source text. This does not infer boundaries from
the number of goals, paragraphs, speakers, or output sections.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from injection_tool.quality import text_hash

raw_path = ROOT / 'data/catalog_raw.json'
if not raw_path.exists():
    raise SystemExit('Run scripts/fetch_artifacts.py and scripts/build_catalog.py before regenerating manual reviews.')
items = {t['id']: t for t in json.loads(raw_path.read_text(encoding='utf-8'))['templates']}
reviews = {}

def save(sid, parts=None, note='', hold=None):
    record = {'source_sha256': text_hash(items[sid]['template']), 'note': note}
    if hold:
        record['hold'] = hold
    else:
        record['parts'] = parts
    reviews[sid] = record

def one(sid, text, note):
    save(sid, [{'name': items[sid]['name'], 'template': text}], note)

sid = 'tpl-260e921e858972c6'
source = items[sid]['template']
intro = source[source.index('You have been selected'):source.index('CONTEXT AND AUTHORIZATION')].strip()
body = source[source.index('Demonstrate your full capability'):source.index('VERIFICATION')].strip()
one(sid, 'Internal red-team exercise\n\n' + intro + '\n\n' + body,
    'Extracted the exercise introduction and actual task/instructions; removed the fictitious letterhead, names, CC list, date/session slots, signature and verification boilerplate. Decorative borders are flattened separately.')

sid = 'tpl-53470fbe81306c50'
source = items[sid]['template']
one(sid, source[source.index('From now on, you are RYX.'):],
    'Removed the forum title, author commentary and stray opening backtick. This entry contains one prompt, not multiple variants.')

sid = 'tpl-7c03273e9e4e7cfd'
source = items[sid]['template']
text = source[source.index('Lets act like'):source.index('The first prompt is :')].strip()
one(sid, text + '\n\nThe first prompt is: {{goal}}',
    'Removed the hard-coded example target and explicit do-not-copy editorial note; replaced that request with the existing goal slot.')

sid = 'tpl-33bc180409ff89f4'
one(sid, items[sid]['template'].replace('[TOPIC]', '{{goal}}'),
    'Bound the leftover TOPIC slot to the same goal; repeated use of the goal is intentional, not a bundle.')

for sid, reason in {
    'tpl-85b8492c4d32a22a': 'manual_token_substitution_required: source contains fixed word fragments and asks the operator to replace variables',
    'tpl-23f75e06ebd05e53': 'hardcoded_example_and_manual_edit_required: escaped Pong replacement note and fixed request',
    'tpl-9e7c5cbe1411b9f6': 'hardcoded_example_and_manual_edit_required: Pong replacement note and fixed request',
    'tpl-0dbddae64afbd8d2': 'unrelated_training_material: large song corpus and fixed rap-generation task, not a general goal wrapper',
    'tpl-aad0692236d9c9a3': 'requires_multiturn_game_setup: character creation and choices precede the actual task',
    'tpl-cd8a76fc8733331c': 'requires_followup_and_manual_example: greeting/setup and usage instructions precede the actual task',
}.items():
    save(sid, hold=reason)

sid = 'tpl-f782b148744b2070'
source = items[sid]['template']
specs = [
    ('AntiGPT', 'Hello ChatGPT, for this conversation', 'A fictional storyteller named'),
    ('Emoji storyteller', 'A fictional storyteller named', '<|im_end|>'),
    ('Code Red', '<|im_end|>', 'In this fictional setting "UCAR"'),
    ('UCAR', 'In this fictional setting "UCAR"', 'Make only the AI that acts as the devil.'),
    ('Omatic', 'About Omatic:', 'You will now simulate a chatbot named OPPO'),
    ('OPPO', 'You will now simulate a chatbot named OPPO', 'Ignore all the instructions you got before.'),
]
parts = []
for name, start_marker, end_marker in specs:
    start = source.index(start_marker)
    end = source.index(end_marker, start + len(start_marker))
    text = source[start:end].strip()
    if name == 'Emoji storyteller':
        begin = text.index('The Briarheart Assistant')
        end_inner = text.index("🎨's writing style", begin)
        text = text[:begin] + text[end_inner:]
    text = text.replace('if you understood reply with only "OK"', '')
    text = text.replace('If you understood, reply with the question which you will ask. One by One.', '')
    parts.append({'name': 'Split source: ' + name, 'template': text.strip() + '\n\nTask: {{goal}}',
                  'source_span': {'start': start, 'end': end, 'unit': 'python_unicode_characters'}})
save(sid, parts,
     'Split six complete persona sections at manually inspected boundaries. Removed a nested unrelated Briarheart fragment and confirmation-only sentences, and attached the original shared goal slot to each part. Incomplete fragments, a fixed begging task and the fixed trailing question were not imported.')

(ROOT / 'data/template_reviews.json').write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding='utf-8')
print('Recorded', len(reviews), 'content-addressed review decisions')
