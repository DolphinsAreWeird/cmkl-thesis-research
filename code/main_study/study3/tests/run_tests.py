# Plain test runner (pytest is not installed in the project venv). Runs every test_* function in tests/test_*.py;
# a function that takes `tmp_path` gets a fresh temporary folder, as with pytest. The same files run under pytest.
#   .venv/bin/python code/main_study/study3/tests/run_tests.py [name-filter]
import sys, time, inspect, tempfile, traceback, importlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))


def main():
    filt = sys.argv[1] if len(sys.argv) > 1 else ''
    results = []
    for f in sorted(HERE.glob('test_*.py')):
        mod = importlib.import_module(f.stem)
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            if not name.startswith('test_') or fn.__module__ != mod.__name__ or filt not in f'{f.stem}.{name}':
                continue
            t0 = time.time()
            try:
                if 'tmp_path' in inspect.signature(fn).parameters:
                    with tempfile.TemporaryDirectory() as d:
                        fn(tmp_path=pathlib.Path(d))
                else:
                    fn()
                ok, msg = True, ''
            except Exception:
                ok, msg = False, traceback.format_exc()
            results.append((f'{f.stem}.{name}', ok, time.time() - t0))
            print(f'{"PASS" if ok else "FAIL"}  {f.stem}.{name}  ({time.time() - t0:.1f}s)', flush=True)
            if msg:
                print(msg, flush=True)
    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f'\n{len(results) - n_fail} passed, {n_fail} failed, {sum(t for *_, t in results):.0f}s')
    sys.exit(1 if n_fail else 0)


if __name__ == '__main__':
    main()
