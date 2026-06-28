.PHONY: test run clean

test:
	pytest -q

run:
	python -m css_probes.cli run-all --out reports/css_probe_report.json

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in map(pathlib.Path, ['.pytest_cache', 'build', 'dist'])]"
