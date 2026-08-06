from pathlib import Path

from douyin_translator.diagnostics import run_diagnostics


if __name__ == "__main__":
    report = run_diagnostics(Path.home() / "Videos" / "Douyin_AI_Translator")
    print(report.as_text())
    raise SystemExit(0 if report.passed else 1)
