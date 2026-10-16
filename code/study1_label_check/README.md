Study 1 label-window check. Run from code/:
  ../.venv/bin/python -m unittest discover -s study1_label_check/tests -v      (tests)
  bash ../jobs/bg.sh s1_labels study1_label_check/run_check.py                  (full run, from project root)
  ../.venv/bin/python study1_label_check/report_tables.py                       (rebuilds data/reports/study1_label_check.md)
Choices the record leaves open are marked `# NOT IN RECORD:` in labels.py and listed in section 6 of the report (notinrecord.txt).
