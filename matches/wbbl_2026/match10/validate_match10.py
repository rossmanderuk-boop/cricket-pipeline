"""
validate_match10.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for WBBL 2026/27 Match 10 (Brisbane Heat Women vs
Adelaide Strikers Women, Drummoyne Oval, Sydney, 2026-11-05).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match10_heat_vs_strikers.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Brisbane Heat Women': {
        'Grace Harris': (22, 18, 4, 0, 'caught'),
        'Charli Knott': (104, 61, 12, 4, 'run out'),
        'Georgia Redmayne': (7, 11, 0, 0, 'lbw'),
        'Yastika Bhatia': (16, 18, 1, 0, 'run out'),
        "Annie O'Neil": (13, 7, 0, 1, 'not out'),
        'Orla Prendergast': (16, 6, 2, 0, 'not out'),
    },
    'Adelaide Strikers Women': {
        'Laura Wolvaardt': (75, 48, 9, 0, 'caught'),
        'Maia Bouchier': (0, 4, 0, 0, 'caught'),
        'Tahlia McGrath': (13, 16, 0, 0, 'caught'),
        'Madeline Penna': (68, 45, 7, 4, 'caught'),
        'Bridget Patterson': (4, 5, 0, 0, 'bowled'),
        'Ellie Johnston': (4, 7, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Brisbane Heat Women': {  # bowled by Adelaide Strikers Women
        'Megan Schutt': (4.0, 36, 0),
        'Eleanor Larosa': (4.0, 48, 1),
        'Sophie Ecclestone': (4.0, 18, 1),
        'Amanda-Jade Wellington': (4.0, 36, 0),
        'Tahlia McGrath': (2.0, 28, 0),
        'Ella Wilson': (1.0, 10, 0),
        'Madeline Penna': (1.0, 6, 0),
    },
    'Adelaide Strikers Women': {  # bowled by Brisbane Heat Women
        'Lily Bassingthwaighte': (2.0, 29, 0),
        'Charli Knott': (4.0, 26, 0),
        'Lucy Hamilton': (4.0, 26, 1),
        'Sarah Glenn': (4.0, 19, 2),
        'Catherine White': (1.0, 10, 0),
        'Sianna Ginger': (3.0, 41, 0),
        'Grace Harris': (2.0, 19, 2),
    },
}

EXPECTED_EXTRAS = {
    'Brisbane Heat Women': {'legbyes': 2, 'noballs': 1, 'wides': 3},
    'Adelaide Strikers Women': {'noballs': 5, 'wides': 1},
}

EXPECTED_TOTALS = {
    'Brisbane Heat Women': (184, 4),
    'Adelaide Strikers Women': (170, 5),
}

# Fall of wickets: (score, player) in order
EXPECTED_FOW = {
    'Brisbane Heat Women': [(57, 'Grace Harris'), (89, 'Georgia Redmayne'),
                            (154, 'Charli Knott'), (156, 'Yastika Bhatia')],
    'Adelaide Strikers Women': [(34, 'Maia Bouchier'), (64, 'Tahlia McGrath'),
                                (141, 'Laura Wolvaardt'), (146, 'Bridget Patterson'),
                                (170, 'Madeline Penna')],
}


def overs_to_balls(overs_str):
    o, _, b = str(overs_str).partition('.')
    return int(o) * 6 + (int(b) if b else 0)


def main():
    d = json.load(open(JSON_PATH))
    all_ok = True

    for inn in d['innings']:
        team = inn['team']
        print(f'=== {team} (batting) ===')

        runs = defaultdict(int); balls = defaultdict(int)
        fours = defaultdict(int); sixes = defaultdict(int); outs = {}
        bowler_balls = defaultdict(int); bowler_runs = defaultdict(int); bowler_wkts = defaultdict(int)
        extras_total = defaultdict(int)

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})

                for k, v in ex.items():
                    extras_total[k] += v

                legal_ball = 'wides' not in ex and 'noballs' not in ex
                if 'wides' not in ex:
                    balls[b] += 1
                if legal_ball:
                    bowler_balls[bwl] += 1
                bowler_runs[bwl] += deliv['runs']['total'] - ex.get('byes', 0) - ex.get('legbyes', 0)

                if not ex or 'noballs' in ex:
                    runs[b] += deliv['runs']['batter']
                    if deliv['runs']['batter'] == 4: fours[b] += 1
                    if deliv['runs']['batter'] == 6: sixes[b] += 1

                for w in deliv.get('wickets', []):
                    outs[w['player_out']] = w['kind']
                    if w['kind'] not in ('run out', 'retired out'):
                        bowler_wkts[bwl] += 1

        print('-- Batting --')
        for name, (er, eb, ef, es, estatus) in EXPECTED_BATTING[team].items():
            ar, ab, af, aS = runs[name], balls[name], fours[name], sixes[name]
            astatus = outs.get(name, 'not out')
            ok = (ar, ab, af, aS) == (er, eb, ef, es) and estatus in astatus
            all_ok &= ok
            print(f"  {name}: got {ar}({ab}) 4s{af} 6s{aS} [{astatus}] vs expected "
                  f"{er}({eb}) 4s{ef} 6s{es} [{estatus}]", 'OK' if ok else '*** MISMATCH ***')

        print('-- Bowling --')
        for name, (eo, er, ew) in EXPECTED_BOWLING[team].items():
            got_overs = f"{bowler_balls[name] // 6}.{bowler_balls[name] % 6}"
            ok = bowler_balls[name] == overs_to_balls(eo) and bowler_runs[name] == er and bowler_wkts[name] == ew
            all_ok &= ok
            print(f"  {name}: got {got_overs}-{bowler_runs[name]}-{bowler_wkts[name]} vs expected "
                  f"{eo}-{er}-{ew}", 'OK' if ok else '*** MISMATCH ***')

        tot = sum(dl['runs']['total'] for o in inn['overs'] for dl in o['deliveries'])
        wk = sum(len(dl.get('wickets', [])) for o in inn['overs'] for dl in o['deliveries'])
        ok = (tot, wk) == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"-- Total: got {tot}/{wk} vs expected {EXPECTED_TOTALS[team][0]}/{EXPECTED_TOTALS[team][1]}",
              'OK' if ok else '*** MISMATCH ***')

        fow = []; running = 0
        for o in inn['overs']:
            for dl in o['deliveries']:
                running += dl['runs']['total']
                for w in dl.get('wickets', []):
                    fow.append((running, w['player_out']))
        ok = fow == EXPECTED_FOW[team]
        all_ok &= ok
        print(f"-- Fall of wickets: {fow}", 'OK' if ok else f'*** MISMATCH *** expected {EXPECTED_FOW[team]}')

        print('-- Extras --')
        for k in extras_total:
            if k not in EXPECTED_EXTRAS[team]:
                all_ok = False
                print(f"  unexpected extras type {k}: {extras_total[k]} *** MISMATCH ***")
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
