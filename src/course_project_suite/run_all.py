from __future__ import annotations
import argparse, json
from course_project_suite.cs188.runner import run as run_cs188
from course_project_suite.coursera_ml.runner import run as run_coursera
from course_project_suite.cs231n.runner import run as run_cs231n
from course_project_suite.d2l.runner import run as run_d2l
from course_project_suite.cs224n.runner import run as run_cs224n
from course_project_suite.cs336.runner import run as run_cs336

RUNNERS=[run_cs188,run_coursera,run_cs231n,run_d2l,run_cs224n,run_cs336]

def run_all():
    return [r() for r in RUNNERS]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--self-check',action='store_true')
    ap.add_argument('--json',action='store_true')
    args=ap.parse_args()
    results=run_all()
    if args.json:
        print(json.dumps({'ok':all(r.ok for r in results),'project_families':len(results),'results':[r.to_dict() for r in results]},indent=2,ensure_ascii=False))
    else:
        for r in results: print(f'{r.name}: {"OK" if r.ok else "FAIL"} {r.metrics}')
    raise SystemExit(0 if all(r.ok for r in results) else 1)

if __name__=='__main__': main()
