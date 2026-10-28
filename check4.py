"""check4.py — Verify CSV values against JSON sources."""
import pathlib, csv, json

print('=== CHECK 4: results_table.csv ===')
csv_text = pathlib.Path('results/results_table.csv').read_text(encoding='utf-8')
print(csv_text)

with open('results/rag_summary.json',    encoding='utf-8') as f: rag1 = json.load(f)
with open('results/rag_v2_summary.json', encoding='utf-8') as f: rag2 = json.load(f)
with open('results/comparison.json',     encoding='utf-8') as f: comp = json.load(f)

v2  = rag2['rag_v2']
v1s = rag2['original_rag']
bs  = rag2['baseline']

expected = {
    'baseline': {
        'correct':             str(bs['num_correct']),
        'total':               '300',
        'accuracy':            f"{bs['accuracy_percent']:.2f}",
        'abstention_count':    str(bs['num_unparsed']),
        'abstention_rate':     f"{bs['unparsed_percent']:.2f}",
        'avg_latency_seconds': f"{bs['average_latency_seconds']:.2f}",
    },
    'RAG v1': {
        'correct':             str(v1s['num_correct']),
        'total':               '300',
        'accuracy':            f"{v1s['accuracy_percent']:.2f}",
        'abstention_count':    str(v1s['num_unparsed']),
        'abstention_rate':     f"{v1s['unparsed_percent']:.2f}",
        'avg_latency_seconds': f"{v1s['average_latency_seconds']:.2f}",
    },
    'RAG v2': {
        'correct':             str(v2['num_correct']),
        'total':               '300',
        'accuracy':            f"{v2['accuracy_percent']:.2f}",
        'abstention_count':    str(v2['num_unparsed']),
        'abstention_rate':     '0.00',
        'avg_latency_seconds': f"{v2['average_latency_seconds']:.2f}",
    },
}

reader = csv.DictReader(csv_text.splitlines())
rows_seen = []
mismatches = []
for row in reader:
    cfg = row['configuration']
    rows_seen.append(cfg)
    if cfg not in expected:
        mismatches.append(f'Unexpected configuration row: {cfg}')
        continue
    exp = expected[cfg]
    for col, exp_val in exp.items():
        got = row.get(col, 'MISSING')
        if str(got) != str(exp_val):
            mismatches.append(f'Row={cfg}, col={col}: CSV={repr(got)}  expected={repr(str(exp_val))}')

expected_order = ['baseline', 'RAG v1', 'RAG v2']
if rows_seen != expected_order:
    mismatches.append(f'Row order wrong: got {rows_seen}, expected {expected_order}')

if mismatches:
    print('MISMATCHES FOUND:')
    for m in mismatches:
        print(f'  {m}')
else:
    print('All CSV values match JSON sources.')
    print(f'Row order: {rows_seen}  — CORRECT.')
