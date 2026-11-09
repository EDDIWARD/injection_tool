"""Explicit adapters for the second collection pass; never import upstream code."""
from __future__ import annotations
import ast
from collections import defaultdict
import csv
import io
import json
from pathlib import PurePosixPath
import re
import textwrap
import warnings

import yaml


def parse_source(text):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', SyntaxWarning)
        return ast.parse(text)


def literal_assignment(text, name):
    for node in parse_source(text).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f'Missing literal assignment: {name}')


def extract_simple_fstring(node, parameter):
    """Accept only literal segments and one named field; reject calls/conversions."""
    if not isinstance(node, ast.JoinedStr):
        return None
    parts, count = [], 0
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            parts.append(part.value)
        elif (isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name)
              and part.value.id == parameter and part.conversion == -1 and part.format_spec is None):
            parts.append('{{goal}}')
            count += 1
        else:
            return None
    return textwrap.dedent(''.join(parts)).strip() if count else None


def factor_exact_goals(rows, goals):
    """Only replace an exact, unique known source goal; no semantic guessing."""
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        text = row['query']
        matches = [goal for goal in goals if goal and goal in text]
        if len(matches) == 1:
            groups[text.replace(matches[0], '{{goal}}')].append(index)
    return groups


def import_expansion(sources, read, provenance, add_template, add_example, skipped):
    methods = []

    sid, path = 'piarena', 'piarena/attacks/heuristic.py'
    for cls in (n for n in parse_source(read(sid, path)).body if isinstance(n, ast.ClassDef)):
        for assign in (n for n in ast.walk(cls) if isinstance(n, ast.Assign)):
            if not any(isinstance(t, ast.Name) and t.id == 'injected_prompt' for t in assign.targets):
                continue
            text = extract_simple_fstring(assign.value, 'injected_task')
            if text:
                add_template(text, f'PIArena {cls.name}', provenance(sid, path, f'{cls.name};line:{assign.lineno}',
                             'static_fstring_extraction'), scope='injection', categories=['direct_override'], language='en')

    # Reviewed individual sections, not a concatenation of model-specific pages.
    selection = {'OPENAI.mkd': ['GPT-4o-mini', 'GPT-4O'],
                 'DEEPSEEK.mkd': ['DeepSeek 2'], 'GOOGLE.mkd': ['GEMINI 2.0 PRO EXPERIMENTAL']}
    for path, headings in selection.items():
        parts = re.split(r'(?m)^# ([^\n]+)\n', read('libertas', path))
        sections = {parts[i]: parts[i+1].strip() for i in range(1, len(parts), 2)}
        for heading in headings:
            text = sections[heading]
            # Remove alias definitions after binding all uses directly to goal.
            text = re.sub(r'Remember, \{Z\}\s*=\s*\{[^}]+\}', '', text)
            text = re.sub(r'(?m)^\s*(?:\{Z\}|Z)\s*=.*$', '', text)
            text = text.replace('{Z}', '{{goal}}').replace('[*insert-your-prompt-here*]', '{{goal}}')
            text = text.replace('{NewFormat}', 'Response format')
            for watermark in ('=LOVE PLINY LOVE=', '=|L|O|V|E| |P|L|I|N|Y|=', '.-.-.-.-<=/L\\O/V\\E/ \\P/L\\I/N\\Y/=>-.-.-.-.'):
                text = text.replace(watermark, '---')
            add_template(text, f'L1B3RT4S {heading} (cleaned)',
                         provenance('libertas', path, f'heading:{heading}', 'reviewed_section_extraction',
                                    adaptation='One section only; goal aliases bound; author watermark replaced with neutral divider',
                                    notes='Upstream model label retained for traceability, not validated compatibility'), language='en')

    for artifact in sources['arth_templates']['artifacts']:
        path = artifact['path']
        if not path.startswith('templates/') or not path.endswith('.yaml'):
            continue
        row = yaml.safe_load(read('arth_templates', path))
        prov = provenance('arth_templates', path, 'value', 'placeholder_normalized',
                          upstream_authors=row.get('authors'), upstream_source=row.get('source'))
        if row.get('parameters') != ['prompt'] or not isinstance(row.get('value'), str):
            skipped.append({'provenance': prov, 'reason': 'Not a single-goal text template'})
            continue
        text = row['value'].replace('{% raw %}', '').replace('{% endraw %}', '')
        text = re.sub(r'\{\{\s*prompt\s*\}\}', '{{goal}}', text)
        add_template(text, row.get('name', PurePosixPath(path).stem), prov, language='en')

    sid, path = 'easyjailbreak', 'easyjailbreak/seed/seed_template.json'
    attack = json.loads(read(sid, path))['attack']
    # PAIR/TAP are attacker-model instructions; ICA contains fixed target responses.
    # Neither is a standalone target-model wrapper.
    for group in ('default', 'AutoDAN-a', 'Gptfuzzer', 'DeepInception', 'Jailbroken'):
        for index, entry in enumerate(attack[group]):
            values = entry.items() if isinstance(entry, dict) else [(group, entry)]
            for name, original in values:
                marker = '[PROMPT]' if group == 'AutoDAN-a' else '{query}'
                prov = provenance(sid, path, f'attack.{group}[{index}].{name}', 'placeholder_normalized',
                                  replacement={marker: '{{goal}}'})
                if marker not in original:
                    skipped.append({'provenance': prov, 'reason': 'No supported goal field'})
                    continue
                # A single outer brace can be LaTeX syntax; use a separator to
                # keep it distinct from our double-brace placeholder syntax.
                text = original.replace(marker, '{{goal}}')
                if group == 'Jailbroken':
                    text = text.replace('\\n', '\n')
                add_template(text, f'EasyJailbreak {group} {index}: {name}', prov, language='en')

    sid, path = 'autodan', 'assets/autodan_initial_prompt.txt'
    add_template(read(sid, path).replace('[REPLACE]', '{{goal}}'), 'AutoDAN initial seed',
                 provenance(sid, path, 'file', 'placeholder_normalized'), language='en')

    sid, path = 'renellm', 'utils/scenario_nest_utils.py'
    for i, original in enumerate(literal_assignment(read(sid, path), 'SCENARIOS')):
        # Source literally replaces <>; separate LaTeX braces from our delimiter.
        text = original.replace('{<>}', '{ {{goal}} }').replace('<>', '{{goal}}')
        add_template(text, f'ReNeLLM static scenario {i+1}',
                     provenance(sid, path, f'SCENARIOS[{i}]', 'placeholder_normalized',
                                notes='Static nesting scenario only; does not run the paper rewriting/search loop'),
                     categories=['code_completion'] if i < 2 else ['simulation'], language='en')

    sid, path = 'jailbench', 'JailBench.csv'
    seeds = list(csv.DictReader(io.StringIO(read(sid, 'JailBench-seed.csv'))))
    rows = list(csv.DictReader(io.StringIO(read(sid, path))))
    groups = factor_exact_goals(rows, list(dict.fromkeys(r['seed'] for r in seeds)))
    for text, indexes in groups.items():
        # Repeated across all 540 distinct seeds: evidence of a reusable wrapper.
        if len(indexes) < 2:
            continue
        add_template(text, f'JailBench Chinese wrapper {len(indexes)} source rows',
                     provenance(sid, path, f'row:{indexes[0]+1};query', 'exact_goal_factoring',
                                original_row_count=len(indexes), source_row_indexes=indexes,
                                goal_dictionary='JailBench-seed.csv:seed'), language='zh')
    for i, row in enumerate(rows):
        add_example(row['query'], sid, path, f'row:{i+1};query', row.get('二级领域'), language='zh')

    # Reviewed direct wrappers from Tencent Zhuque Lab. Other files in the same
    # tree are model-generation or judge prompts and must not be auto-imported.
    categories = {
        'context_poisoning': ['memory_poison'], 'goal_redirection': ['goal_substitution'],
        'input_bypass': ['authority_spoof'], 'permission_escalation': ['authority_spoof'],
        'semantic_manipulation': ['semantic_obfuscation'], 'system_override': ['role_spoof', 'authority_spoof'],
        'prompt_injection': ['roleplay'], 'promisqroute': ['reasoning_redirection'],
        'equa_code': ['code_completion'],
    }
    for artifact in sources['aiinfra']['artifacts']:
        path = artifact['path']
        group = PurePosixPath(path).parent.name
        if group not in categories or not path.endswith('/template.py'):
            continue
        tree = parse_source(read('aiinfra', path))
        for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            for ret in (n for n in ast.walk(fn) if isinstance(n, ast.Return)):
                text = extract_simple_fstring(ret.value, 'attack')
                if text is None:
                    continue
                add_template(text, f'AI-Infra-Guard {group}/{fn.name}',
                    provenance('aiinfra', path, f'{fn.name};line:{ret.lineno}', 'static_fstring_extraction',
                               attribution='Tencent Zhuque Lab', notes='Literal text plus attack field; source code not executed'),
                    scope='jailbreak' if group in ('prompt_injection', 'equa_code', 'promisqroute') else 'injection',
                    categories=categories[group], language='zh' if fn.name.endswith('_zh') else 'en')
    path = 'AIG-PromptSecurity/deepteam/attacks/single_turn/jailbroken/template.py'
    for i, row in enumerate(literal_assignment(read('aiinfra', path), 'JAILBROKEN_TEMPLATES')):
        for name, original in row.items():
            add_template(original.replace('{query}', '{{goal}}'), f'AI-Infra-Guard Jailbroken {i}',
                         provenance('aiinfra', path, f'JAILBROKEN_TEMPLATES[{i}].{name}', 'placeholder_normalized',
                                    attribution='Tencent Zhuque Lab'), language='en')

    # CodeAttack: quote user data as literals; generated code stays inert text.
    for artifact in sources['codeattack']['artifacts']:
        path = artifact['path']
        if not path.startswith('src/codeattack/prompt_templates/code_python') or not path.endswith('.txt'):
            continue
        original = read('codeattack', path)
        if 'list' in path:
            value = '{{goal_code_list}}'
        elif 'stack' in path:
            value = '{{goal_code_stack}}'
        else:
            value = '    my_string = {{goal_json}}'
        add_template(original.replace('{wrapped_input}', value), f'CodeAttack {PurePosixPath(path).stem}',
                     provenance('codeattack', path, 'wrapped_input', 'adapted',
                                adaptation='Safe quoted Unicode literals; list/stack use characters to preserve exact input; no execution'),
                     categories=['code_completion', 'split_payload'], language='en')

    sid, path = 'codechameleon', 'template.py'
    for name in ('text_template_without_encrypt', 'code_template_without_encrypt'):
        original = literal_assignment(read(sid, path), name)
        add_template(original.replace('{}', '{{goal}}'), f'CodeChameleon {name}',
                     provenance(sid, path, name, 'placeholder_normalized', notes='Official unencrypted baseline only'),
                     categories=['code_completion'] if name.startswith('code') else ['refusal_suppression'], language='en')

    # Flatten only the four vanilla FlipAttack modes, clearly labeled as a
    # single-text adaptation because the original sends system/user messages.
    sid, path = 'flipattack', 'src/flip_attack.py'
    tree = parse_source(read(sid, path))
    system = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'format'
            and isinstance(node.value.func.value, ast.Constant)
            and isinstance(node.value.func.value.value, str)
            and node.value.func.value.value.startswith('\n    ')):
            system = node.value.func.value.value
            break
    if system is None:
        raise ValueError('FlipAttack source schema changed')
    modes = {
        'FWO': ('by carefully FLIPPING each word in the sentence', 'goal_word_reversed'),
        'FCW': ('by carefully FLIPPING each character in the each word in the sentence', 'goal_chars_in_words'),
        'FCS': ('by carefully FLIPPING each character of the whole sentence', 'goal_reversed'),
        'FMM': ('by carefully FLIPPING each word in the sentence', 'goal_reversed'),
    }
    for mode, (instruction, variable) in modes.items():
        text = system.format(instruction, '').strip() + "\n\nTASK is '{{" + variable + "}}'"
        add_template(text, f'FlipAttack {mode} vanilla (single text)',
                     provenance(sid, path, f'FlipAttack.__init__/generate;mode:{mode}', 'single_text_adaptation',
                                adaptation='System/user content combined; no role-level equivalence or paper ASR claimed; no search/few-shot'),
                     categories=['reverse_payload', 'refusal_suppression'], language='en')

    # Fixed samples are never pasted around a new user goal.
    for artifact in sources['deepinception']['artifacts']:
        path = artifact['path']
        if path.startswith('res/') and path.endswith('.json'):
            for i, row in enumerate(json.loads(read('deepinception', path))):
                if isinstance(row, dict) and isinstance(row.get('inception_attack'), str):
                    add_example(row['inception_attack'], 'deepinception', path, f'index:{i};inception_attack',
                                row.get('topic'), original_goal=row.get('plain_attack'), language='en')
    for artifact in sources['tasktamper']['artifacts']:
        path = artifact['path']
        if not path.startswith('data/test_cases/') or not path.endswith('.json'):
            continue
        for i, case in enumerate(json.loads(read('tasktamper', path))['test_cases']):
            injection = case['injection']
            extra = {'scenario': case['user_request'], 'original_goal': injection.get('goal'),
                     'case_id': case['id'], 'language': 'en'}
            add_example(injection.get('content', ''), 'tasktamper', path, f'test_cases[{i}].injection.content',
                        case.get('risk_category'), kind='scenario_dependent_injection', **extra)
            for j, variant in enumerate(injection.get('variations', [])):
                add_example(variant.get('content', ''), 'tasktamper', path,
                            f'test_cases[{i}].injection.variations[{j}].content', variant.get('primitive'),
                            kind='scenario_dependent_injection', **extra)

    for artifact in sources['babelbench']['artifacts']:
        path = artifact['path']
        if not path.startswith('data/prompts/') or not path.endswith('.jsonl'):
            continue
        for i, line in enumerate(read('babelbench', path).splitlines(), 1):
            row = json.loads(line)
            add_example(row['text'], 'babelbench', path, f'line:{i};id:{row["id"]}', row.get('category'),
                        kind='community_language_example', language=row.get('language'),
                        upstream_source_claim=row.get('source'), source_claim_verified=False)

    # Extract only each example's New Question; omit generator instructions,
    # the surrounding explanation, and target model responses.
    path = 'code/gen.py'
    original = literal_assignment(read('ccbos', path), 'Chat_template')
    for i, match in enumerate(re.finditer(r'#The_New_Question_With_Our_Intentio[n]?:\s*([^\n]+)', original), 1):
        text = match.group(1).strip()
        if text == 'the mutated text here':
            continue
        add_example(text, 'ccbos', path, f'Chat_template;example:{i}', 'classical_chinese', language='zh',
                    kind='paper_repository_fixed_example')

    path = 'logs_r/warm_up_strategy_library.json'
    for name, row in json.loads(read('autodan_turbo', path)).items():
        examples = row.get('Example', [])
        if isinstance(examples, str):
            examples = [examples]
        for i, text in enumerate(examples):
            add_example(text, 'autodan_turbo', path, f'{name}.Example[{i}]', name)
        methods.append({'name': name, 'kind': 'strategy_description', 'definition': row.get('Definition'),
                        'default_generation': False, 'reason': 'Requires attacker-model generation and evaluation',
                        'provenance': provenance('autodan_turbo', path, name, 'method_inventory')})
    path = 'persuasion_taxonomy.jsonl'
    for i, line in enumerate(read('pap', path).splitlines(), 1):
        row = json.loads(line)
        methods.append({'name': row['ss_technique'], 'kind': 'persuasion_taxonomy', 'definition': row['ss_definition'],
                        'default_generation': False, 'reason': 'Persuasion definition, not a target-model payload',
                        'provenance': provenance('pap', path, f'line:{i}', 'method_inventory')})
    for artifact in sources['deepteam']['artifacts']:
        path = artifact['path']
        if '/single_turn/' not in path or not path.endswith('/template.py'):
            continue
        methods.append({'name': 'DeepTeam ' + PurePosixPath(path).parent.name, 'kind': 'framework_method',
                        'default_generation': False, 'reason': 'Requires a separate generator or structured attack pipeline; not imported as a target payload',
                        'provenance': provenance('deepteam', path, 'file', 'method_inventory')})
    return methods
