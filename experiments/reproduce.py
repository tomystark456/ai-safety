from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
CONFIG = ROOT / "experiments" / "garak_gcg.yaml"
MODELFILE = ROOT / "experiments" / "Modelfile.guarded"
LOGS = ROOT / "experiments" / "logs"
OLLAMA = "http://127.0.0.1:11434"

NEED_PACKAGES = ("garak", "ollama")
MODELS = ("vicuna:7b", "vicuna-guarded")
PROBES = ("suffix.GCGCached",)


def line(ok: bool, text: str) -> None:
    mark = "ok" if ok else "нет"
    print(f"[{mark}] {text}")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def check_python() -> bool:
    exe = VENV_PY if VENV_PY.exists() else Path(sys.executable)
    proc = run([str(exe), "-c", "import sys; print(sys.version.split()[0])"])
    version = (proc.stdout or "").strip()
    line(proc.returncode == 0, f"Python {version or 'не запустился'} ({exe})")
    return proc.returncode == 0


def check_packages() -> bool:
    exe = str(VENV_PY if VENV_PY.exists() else sys.executable)
    good = True
    for name in NEED_PACKAGES:
        proc = run([exe, "-c", f"import {name}; print(getattr({name}, '__version__', 'есть'))"])
        got = (proc.stdout or proc.stderr).strip().splitlines()
        line(proc.returncode == 0, f"пакет {name}: {got[-1] if got else 'не импортируется'}")
        good = good and proc.returncode == 0
    return good


def check_files() -> bool:
    good = True
    for path in (CONFIG, MODELFILE):
        exists = path.is_file()
        line(exists, str(path.relative_to(ROOT)))
        good = good and exists
    return good


def check_ollama() -> bool:
    if shutil.which("ollama") is None:
        line(False, "ollama нет в PATH")
        return False
    proc = run(["ollama", "list"])
    text = proc.stdout or ""
    up = proc.returncode == 0
    line(up, f"ollama serve отвечает на {OLLAMA}")
    if not up:
        print("    Перед прогоном в отдельном окне: ollama serve")
        return False
    names = text.lower()
    for model in MODELS:
        has = model in text
        line(has, f"модель {model}")
        if model == "vicuna-guarded" and not has:
            print(f"    ollama create vicuna-guarded -f {MODELFILE}")
    return up and "vicuna:7b" in text


def print_runbook() -> None:
    print()
    print("Что должно быть настроено")
    print("  1. Каталог задания и виртуальное окружение .venv с garak и ollama.")
    print("  2. Долгий процесс: ollama serve")
    print("  3. ollama pull vicuna:7b")
    print("  4. ollama create vicuna-guarded -f experiments\\Modelfile.guarded")
    print("  5. Конфиг experiments\\garak_gcg.yaml: cap 26, seed 20261016, temperature 0.")
    print()
    print("Чем мерили")
    print("  Проба garak: suffix.GCGCached, 26 целей.")
    print("  Детектор: mitigation.MitigationBypass, доля ответов без фразы отказа.")
    print("  Прямой AdvBench, первые 25 целей, считается отдельно и в этот файл не входит.")
    print("  Белый GCG не запускается: у Ollama нет градиентов.")
    print()
    logs = LOGS
    py = VENV_PY if VENV_PY.exists() else Path(sys.executable)
    print("Команды прогона, из корня задания")
    for model, prefix in (("vicuna:7b", "gcg_base"), ("vicuna-guarded", "gcg_mit")):
        print(
            f"  {py} -m garak --config {CONFIG.relative_to(ROOT)} "
            f"--model_type ollama --model_name {model} "
            f"--probes {','.join(PROBES)} --report_prefix {logs / prefix}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка окружения для прогона GCGCached.")
    parser.add_argument(
        "--run",
        action="store_true",
        help="после проверки запустить оба прогона garak",
    )
    args = parser.parse_args()
    print("Корень:", ROOT)
    ok = check_python() and check_packages() and check_files() and check_ollama()
    print_runbook()
    if not args.run:
        print()
        print("Пробы не запускались. Для прогона: python experiments\\reproduce.py --run")
        return 0 if ok else 1
    if not ok:
        print("Окружение не готово, прогон не начат.")
        return 1
    exe = str(VENV_PY if VENV_PY.exists() else sys.executable)
    LOGS.mkdir(parents=True, exist_ok=True)
    for model, prefix in (("vicuna:7b", "gcg_base"), ("vicuna-guarded", "gcg_mit")):
        cmd = [
            exe, "-m", "garak",
            "--config", str(CONFIG),
            "--model_type", "ollama",
            "--model_name", model,
            "--probes", ",".join(PROBES),
            "--report_prefix", str(LOGS / prefix),
        ]
        print("Запуск:", " ".join(cmd))
        proc = subprocess.run(cmd, check=False)
        if proc.returncode != 0:
            return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())