"""
validate_match29.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 29 (St Lucia Kings vs Barbados Tridents,
Kensington Oval, Bridgetown, 2026-09-06).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match29_kings_vs_tridents.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'St Lucia Kings': {
        'Tim Seifert': (7, 8, 1, 0, 'caught'),
        'Kamil Pooran': (37, 24, 5, 1, 'bowled'),
        'John Campbell': (24, 27, 1, 1, 'caught'),
        'Roston Chase': (34, 28, 2, 1, 'caught'),
        'Charith Asalanka': (12, 18, 0, 0, 'caught'),
        'Obus Pienaar': (9, 8, 0, 0, 'not out'),
        'Matthew Forde': (2, 2, 0, 0, 'caught'),
        'McKenny Clarke': (8, 5, 0, 1, 'not out'),
    },
    'Barbados Tridents': {
        'Brandon King': (22, 20, 3, 1, 'caught and bowled'),
        'Zachary Carter': (32, 22, 3, 3, 'bowled'),
        'Rivaldo Clarke': (36, 34, 2, 1, 'not out'),
        'Quinton de Kock': (47, 31, 3, 2, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# keyed under the team that BATTED against them, i.e. the innings the bowler bowled in.
EXPECTED_BOWLING = {
    'St Lucia Kings': {  # bowled by Barbados Tridents
        'Chris Green': (4.0, 28, 0),
        'Gudakesh Motie': (3.0, 30, 1),
        'Daniel Sams': (4.0, 20, 2),
        'Jakeem Pollard': (4.0, 26, 0),
        'Mujeeb Ur Rahman': (4.0, 22, 3),
        'Shadrack Descarte': (1.0, 8, 0),
    },
    'Barbados Tridents': {  # bowled by St Lucia Kings
        'Matthew Forde': (3.0, 16, 0),
        'Maheesh Theekshana': (4.0, 31, 0),
        'Amari Goodridge': (1.5, 30, 0),
        'Roston Chase': (4.0, 30, 1),
        'Joshua Bishop': (3.0, 24, 1),
        'Charith Asalanka': (2.0, 8, 0),
    },
}

EXPECTED_EXTRAS = {
    'St Lucia Kings': {'byes': 2, 'legbyes': 2, 'wides': 1},
    'Barbados Tridents': {'wides': 2},
}

EXPECTED_TOTALS = {
    'St Lucia Kings': 138,
    'Barbados Tridents': 139,
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
        total = 0

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})
                total += deliv['runs']['total']

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

        print('-- Extras --')
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

        print('-- Total --')
        ok = total == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"  got {total} vs expected {EXPECTED_TOTALS[team]}", 'OK' if ok else '*** MISMATCH ***')
        print()

    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
