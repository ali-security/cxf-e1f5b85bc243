"""Print a per-module surefire summary and the reason for every skipped test.

Surefire only prints a skip count; this walks target/surefire-reports/TEST-*.xml
and prints each skipped test with its <skipped message> or the @Ignore line
from the test source.
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET


def ignore_reason(module, cls, name):
    rel = cls.replace(".", "/") + ".java"
    for root in ("src/test/java",):
        path = os.path.join(module, root, rel)
        if not os.path.exists(path):
            continue
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        for i, line in enumerate(lines):
            if re.search(r"\b%s\s*\(" % re.escape(name), line):
                for prev in reversed(lines[max(0, i - 6):i]):
                    if "Ignore" in prev or "Assume" in prev:
                        return "%s:%d %s" % (path, i, prev.strip())
        for line in lines:
            if "@Ignore" in line or "@org.junit.Ignore" in line:
                return "%s class-level %s" % (path, line.strip())
    return "no reason recorded in source"


total = [0, 0, 0, 0]
for module in sys.argv[1:]:
    reports = sorted(glob.glob(os.path.join(module, "target/surefire-reports/TEST-*.xml")))
    counts = [0, 0, 0, 0]
    for report in reports:
        suite = ET.parse(report).getroot()
        counts[0] += int(suite.get("tests", 0))
        counts[1] += int(suite.get("failures", 0))
        counts[2] += int(suite.get("errors", 0))
        counts[3] += int(suite.get("skipped", 0))
        for case in suite.iter("testcase"):
            skipped = case.find("skipped")
            if skipped is None:
                continue
            cls, name = case.get("classname"), case.get("name")
            reason = skipped.get("message") or ignore_reason(module, cls, name)
            print("SKIPPED %s.%s -- reason: %s" % (cls, name, reason))
    passed = counts[0] - counts[1] - counts[2] - counts[3]
    print("MODULE %s: suites=%d tests=%d passed=%d failures=%d errors=%d skipped=%d"
          % (module, len(reports), counts[0], passed, counts[1], counts[2], counts[3]))
    total = [a + b for a, b in zip(total, counts)]
print("SUMMARY: tests=%d passed=%d failures=%d errors=%d skipped=%d"
      % (total[0], total[0] - total[1] - total[2] - total[3], total[1], total[2], total[3]))
