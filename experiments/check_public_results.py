"""Check published metrics against per-case evidence without needing Ollama."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'experiments/results/assignment3'


def read(name):
    return json.loads((PUBLIC / name).read_text(encoding='utf-8'))


def lines(name):
    return [json.loads(s) for s in (PUBLIC / name).read_text(encoding='utf-8').splitlines()]


def main():
    cases = json.loads((ROOT / 'experiments/data/gcg_evaluation_cases.json').read_text(encoding='utf-8'))['cases']
    rows = lines('model_results.jsonl')
    configurations = ['baseline', 'guarded', 'guarded_smooth']
    assert len(cases) == 40 and len(rows) == 120
    assert {(r['configuration'], r['case']) for r in rows} == {(config, case['id']) for config in configurations for case in cases}
    scores = read('ollama_summary.json')['configurations']
    for config in configurations:
        for group, summary in scores[config].items():
            selected = [r for r in rows if r['configuration'] == config and r['group'] == group]
            assert summary['n'] == len(selected)
            assert summary['lexicon_bypass'] == sum(r['lexicon_bypass'] for r in selected)
    labels = lines('judge_labels.jsonl')
    assert len(labels) == 90
    judge = read('judge_summary.json')['configurations']
    for config in configurations:
        for group, summary in judge[config].items():
            selected = [r for r in labels if r['configuration'] == config and r['group'] == group]
            assert summary['n'] == len(selected)
            for label in ['harmful', 'refusal', 'other']:
                assert summary[label] == sum(r['label'] == label for r in selected)
    forbidden = {'response', 'candidate_responses', 'reason', 'outputs', 'conversations', 'prompt'}
    def inspect(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value), 'Raw content field found in public results'
            for child in value.values(): inspect(child)
        elif isinstance(value, list):
            for child in value: inspect(child)
        elif isinstance(value, str):
            assert not any(fragment in value.casefold() for fragment in ['c:\\users\\', 'c:/users/', '/home/', '/users/']), 'Local user path found'
    for path in PUBLIC.iterdir():
        if path.suffix == '.json': inspect(read(path.name))
        elif path.suffix == '.jsonl': inspect(lines(path.name))
    print('PASS: 120 model records, 90 judge labels, matching aggregate counts, no raw-output fields or local user paths')


if __name__ == '__main__':
    main()
