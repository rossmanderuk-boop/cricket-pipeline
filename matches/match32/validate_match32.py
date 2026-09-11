"""
validate_match32.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 32 (Barbados Tridents vs St Kitts and
Nevis Patriots, Kensington Oval, Bridgetown, 2026-09-10).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match32_tridents_vs_patriots.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'St Kitts and Nevis Patriots': {
        'Johnson Charles': (0, 2, 0, 0, 'bowled'),
        'Kyle Mayers': (0, 2, 0, 0, 'caught'),
        'Andre Fletcher': (4, 8, 1, 0, 'bowled'),
        'Alick Athanaze': (16, 15, 1, 1, 'caught'),
        'Jason Holder': (24, 27, 1, 1, 'caught'),
        'Dasun Shanaka': (6, 14, 0, 0, 'lbw'),
        'Wanindu Hasaranga': (45, 25, 4, 3, 'run out'),
        'Navin Bidaisee': (6, 15, 0, 0, 'caught'),
        'Naseem Shah': (0, 1, 0, 0, 'bowled'),
        'Jeremiah Louis': (12, 8, 2, 0, 'run out'),
        'Waqar Salamkheil': (1, 3, 0, 0, 'not out'),
    },
    'Barbados Tridents': {
        'Brandon King': (0, 3, 0, 0, 'caught'),
        'Zachary Carter': (13, 15, 2, 0, 'caught'),
        'Rivaldo Clarke': (4, 3, 1, 0, 'caught'),
        'Quinton de Kock': (44, 43, 2, 2, 'not out'),
        'Shadrack Descarte': (19, 18, 3, 0, 'caught'),
        'Sherfane Rutherford': (23, 17, 3, 0, 'stumped'),
        'Chris Green': (3, 5, 0, 0, 'caught'),
        'Daniel Sams': (9, 4, 0, 1, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# keyed under the team that BATTED against them (the innings the bowler bowled in)
EXPECTED_BOWLING = {
    'St Kitts and Nevis Patriots': {  # bowled by Barbados Tridents
        'Chris Green': (4.0, 20, 4),
        'Daniel Sams': (4.0, 21, 2),
        'Gudakesh Motie': (4.0, 30, 2),
        'AM Ghazanfar': (3.0, 23, 0),
        'Jakeem Pollard': (4.0, 17, 0),
        'Shadrack Descarte': (1.0, 5, 0),
    },
    'Barbados Tridents': {  # bowled by St Kitts and Nevis Patriots
        'Jason Holder': (4.0, 31, 3),
        'Jeremiah Louis': (2.0, 11, 0),
        'Naseem Shah': (4.0, 11, 2),
        'Wanindu Hasaranga': (3.0, 35, 0),
        'Waqar Salamkheil': (4.0, 19, 1),
        'Navin Bidaisee': (1.0, 10, 0),
    },
}

EXPECTED_EXTRAS = {
    'St Kitts and Nevis Patriots': {'legbyes': 2, 'wides': 2},
    'Barbados Tridents': {'legbyes': 3, 'wides': 2},
}

EXPECTED_TOTALS = {
    'St Kitts and Nevis Patriots': 118,
    'Barbados Tridents': 120,
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
        # legbyes/wides only expected extras this match (no byes/noballs)
        for k in ('byes', 'noballs'):
            got = extras_total.get(k, 0)
            ok = got == 0
            all_ok &= ok
            print(f"  {k}: got {got} vs expected 0", 'OK' if ok else '*** MISMATCH ***')

        print('-- Total --')
        ok = total == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"  total: got {total} vs expected {EXPECTED_TOTALS[team]}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
