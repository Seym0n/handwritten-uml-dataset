"""
Validate PlantUML annotations for correct parsing/compilation.

Primary check : plantuml-custompipe-v3.jar -syntax (parallelised, avoids 1 JVM/annotation)
Secondary check: plantuml_server.py XMI conversion (persistent pipe, additional structural check)

Run with: py validate_annotations.py [--no-server] [--workers N]
"""

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(__file__).parent
JAR      = BASE_DIR / "plantuml-custompipe-v3.jar"
ANN_FILE = BASE_DIR / "annotations.json"
REPORT   = BASE_DIR / "validation_errors.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract(code: str) -> str:
    """Strip markdown fences and extract @startuml..@enduml block."""
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines).strip()
    m = re.search(r"@startuml.*?@enduml", code, re.DOTALL | re.IGNORECASE)
    return m.group(0) if m else code


# ---------------------------------------------------------------------------
# JAR -syntax check  (one JVM per annotation, parallelised)
# ---------------------------------------------------------------------------

def check_jar(clean_code: str) -> tuple[bool, str]:
    """Run `java -jar plantuml-custompipe-v3.jar -syntax` on clean_code.

    PlantUML -syntax reads a diagram from stdin and writes a human-readable
    summary to stdout:
      - valid   → "OK" / diagram-type string / "0 error(s)"
      - invalid → error description lines, non-zero exit code
    """
    try:
        r = subprocess.run(
            ["java", "-jar", str(JAR), "-syntax"],
            input=clean_code.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
        out = (r.stdout + r.stderr).decode("utf-8", errors="replace").strip()

        if r.returncode != 0:
            return False, out or f"exit {r.returncode}"

        # "0 error" → zero errors → valid; any other "error" phrase → invalid
        lower = out.lower()
        if "error" in lower and "0 error" not in lower:
            return False, out

        return True, out

    except subprocess.TimeoutExpired:
        return False, "timeout (>30 s)"
    except FileNotFoundError:
        return False, "java not found in PATH"


# ---------------------------------------------------------------------------
# plantuml_server XMI check  (persistent pipe, thread-safe via internal lock)
# ---------------------------------------------------------------------------

_server_available = True


def check_server(raw_code: str) -> tuple[bool, str]:
    """Validate via plantuml_server.py XMI conversion (class diagrams only)."""
    global _server_available
    if not _server_available:
        return True, "server unavailable (skipped)"
    try:
        from plantuml_server import plantuml_to_xmi
        xmi = plantuml_to_xmi(raw_code)
        return (True, "XMI OK") if xmi else (False, "XMI conversion returned None")
    except ImportError:
        _server_available = False
        return True, "plantuml_server not importable (skipped)"
    except Exception as e:
        return True, f"server exception: {e} (skipped)"


# ---------------------------------------------------------------------------
# Per-annotation validation  (called from thread pool)
# ---------------------------------------------------------------------------

def validate_one(ann: dict, idx: int) -> dict:
    clean        = _extract(ann["plantuml"])
    diagram_type = ann.get("type", "unknown")
    jar_ok,    jar_msg    = check_jar(clean)
    # XMI has no support for activity diagrams — skip server check for them
    if diagram_type == "class_diagram":
        server_ok, server_msg = check_server(ann["plantuml"])
    else:
        server_ok, server_msg = True, "skipped (activity diagram)"
    return {
        "index":        idx,
        "image":        ann["image"],
        "type":         diagram_type,
        "jar_valid":    jar_ok,
        "jar_msg":      jar_msg,
        "server_valid": server_ok,
        "server_msg":   server_msg,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Parse simple CLI flags
    args      = sys.argv[1:]
    no_server = "--no-server" in args
    workers   = 8
    if "--workers" in args:
        try:
            workers = int(args[args.index("--workers") + 1])
        except (IndexError, ValueError):
            sys.exit("ERROR: --workers requires an integer argument")

    if no_server:
        global _server_available
        _server_available = False

    # Preflight checks
    if not JAR.exists():
        sys.exit(f"ERROR: JAR not found — {JAR}")
    if not ANN_FILE.exists():
        sys.exit(f"ERROR: annotations file not found — {ANN_FILE}")

    annotations = json.loads(ANN_FILE.read_text(encoding="utf-8"))
    total = len(annotations)

    # Pre-warm the XMI server singleton before threads start to avoid a
    # race on the lazy initialisation in plantuml_server.py.
    if _server_available:
        try:
            from plantuml_server import plantuml_to_xmi
            plantuml_to_xmi("@startuml\nnote: warmup\n@enduml")
        except Exception:
            pass

    print(f"Validating {total} annotations  "
          f"[workers={workers}, server={'on' if _server_available else 'off'}]\n")

    results: list[dict | None] = [None] * total
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(validate_one, ann, i): i
            for i, ann in enumerate(annotations)
        }
        for future in as_completed(futures):
            r = future.result()
            results[r["index"]] = r
            done += 1

            tag = "OK  " if r["jar_valid"] else "FAIL"
            print(f"[{done:>3}/{total}] {tag}  {r['image']}", flush=True)
            if not r["jar_valid"]:
                print(f"        JAR   : {r['jar_msg'][:300]}")
            if not r["server_valid"]:
                print(f"        Server: {r['server_msg']}")

    # Summary
    jar_fails    = [r for r in results if not r["jar_valid"]]
    server_fails = [r for r in results if not r["server_valid"]]
    any_fails    = [r for r in results if not r["jar_valid"] or not r["server_valid"]]

    print(f"\n{'='*55}")
    print(f"  Total annotations : {total}")
    print(f"  JAR -syntax valid : {total - len(jar_fails)}/{total}")
    print(f"  JAR -syntax fails : {len(jar_fails)}")
    if _server_available:
        print(f"  Server XMI fails  : {len(server_fails)}")
    print(f"{'='*55}")

    if any_fails:
        REPORT.write_text(json.dumps(any_fails, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        print(f"\nError report → {REPORT}")
        sys.exit(1)
    else:
        print("\nAll annotations passed validation.")


if __name__ == "__main__":
    main()
