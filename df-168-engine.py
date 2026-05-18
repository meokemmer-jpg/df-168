
# K16: Concurrent-Spawn-Mutex (fcntl-based, Trinity-CONSERVATIVE 2026-05-17)
def k16_lock_or_exit(df_name: str):
    """Acquire exclusive lock or exit(3). Prevents concurrent DF runs."""
    import fcntl, os, sys
    lock_path = f"/tmp/df-trinity-{df_name}.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        sys.exit(3)


# K13: External-Anchor-Mock-RFC3161 (Trinity-CONSERVATIVE 2026-05-17)
def k13_anchor(payload_hash: str) -> dict:
    """Mock RFC3161-style timestamp anchor."""
    from datetime import datetime, timezone
    return {
        "anchor_type": "rfc3161-mock",
        "iso_ts": datetime.now(timezone.utc).isoformat(),
        "payload_hash": payload_hash,
    }


# K12: HMAC-SHA256-Provenance (Trinity-CONSERVATIVE 2026-05-17)
def k12_provenance(payload: bytes, key: bytes = b"df-trinity-conservative-v1") -> dict:
    """Returns payload_hash + HMAC-SHA256 signature."""
    import hashlib, hmac
    return {
        "payload_hash": hashlib.sha256(payload).hexdigest(),
        "hmac_sha256": hmac.new(key, payload, hashlib.sha256).hexdigest(),
    }

"""DF-168 engine for book-writing progress tracking."""

import re
import os
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timezone


DF_DIR = Path(__file__).parent
LOCK_DIR = Path("/tmp/df-168.lock")
DF_ID = "168"
DECISION_KEYWORDS_REGEX = re.compile(
    r"\b(entscheid[a-z]*|empfehl(?:e|en|t|st)|sollt(?:e|en|est)|recommend[a-z]*|decid[a-z]*|advis[a-z]*|propos[a-z]*)\b",
    re.IGNORECASE,
)


@dataclass
class TrackerOutput:
    welle: str = "25"
    df: str = "DF-168"
    iso_timestamp: str = ""
    source: str = "mock"
    books_active: int = 0
    words_written_total: int = 0
    words_target_per_book: dict = field(default_factory=dict)
    completion_pct: dict = field(default_factory=dict)
    last_writing_session: dict = field(default_factory=dict)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_stable(path, min_age_sec=300) -> bool:
    p = Path(path)
    try:
        stat = p.stat()
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return (time.time() - stat.st_mtime) >= min_age_sec


def acquire_lock_with_identity() -> bool:
    stale_after_sec = 6 * 60 * 60
    now = time.time()

    try:
        LOCK_DIR.mkdir(mode=0o700)
        _write_lock_identity()
        return True
    except FileExistsError:
        pass
    except OSError:
        return False

    try:
        stat = LOCK_DIR.stat()
        if now - stat.st_mtime > stale_after_sec:
            _remove_lock_dir()
            LOCK_DIR.mkdir(mode=0o700)
            _write_lock_identity()
            return True
    except FileExistsError:
        return False
    except FileNotFoundError:
        try:
            LOCK_DIR.mkdir(mode=0o700)
            _write_lock_identity()
            return True
        except OSError:
            return False
    except OSError:
        return False

    return False


def _write_lock_identity() -> None:
    identity = {
        "df_id": DF_ID,
        "pid": os.getpid(),
        "created_at": iso_now(),
        "cwd": os.getcwd(),
    }
    try:
        (LOCK_DIR / "identity.json").write_text(
            json.dumps(identity, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except OSError:
        pass


def _remove_lock_dir() -> None:
    if not LOCK_DIR.exists():
        return

    for child in LOCK_DIR.iterdir():
        try:
            if child.is_file() or child.is_symlink():
                child.unlink()
        except OSError:
            pass

    try:
        LOCK_DIR.rmdir()
    except OSError:
        pass


def release_lock() -> None:
    try:
        identity_path = LOCK_DIR / "identity.json"
        if identity_path.exists():
            identity_path.unlink()
        LOCK_DIR.rmdir()
    except OSError:
        pass


def k17_pre_action_verification(anchors) -> dict:
    """K17 Pre-Action-Verification (Welle-28-Fix: Path.exists() check)."""
    env_tag = os.environ.get("DF_ENV_TAG", "dev")
    missing = [str(a) for a in anchors if not Path(str(a)).exists()]
    return {"ok": len(missing) == 0, "missing_anchors": missing, "env_tag": env_tag}

    checks = {
        "DF_DIR": DF_DIR.exists(),
        "DF_ID": DF_ID == "168",
        "LOCK_PARENT": LOCK_DIR.parent.exists(),
    }

    for anchor in expected:
        if anchor in checks and not checks[anchor]:
            missing.append(anchor)
        elif anchor not in checks and not anchor:
            missing.append(anchor)

    return {
        "ok": not missing,
        "missing_anchors": missing,
        "env_tag": "real" if _is_real_api_enabled() else "mock",
    }


def _is_real_api_enabled() -> bool:
    raw = os.environ.get("DF_168_REAL_API_ENABLED", "false").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def scan_output_for_decision_keywords(text) -> list:
    if not text:
        return []
    return sorted({match.group(0) for match in DECISION_KEYWORDS_REGEX.finditer(text)})


def assert_no_decision_keywords(output) -> None:
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False, sort_keys=True)
    hits = scan_output_for_decision_keywords(output)
    if hits:
        raise ValueError("Q_0/K_0 violation: blocked keywords found: " + ", ".join(hits))


def collect_tracker_output() -> TrackerOutput:
    result = TrackerOutput(iso_timestamp=iso_now())

    if _is_real_api_enabled():
        result.source = "real"
        real_path = Path(os.environ.get("DF_168_REAL_API_PATH", "")).expanduser()
        if real_path and real_path.exists() and _file_stable(real_path, min_age_sec=0):
            payload = json.loads(real_path.read_text(encoding="utf-8"))
            result.books_active = int(payload.get("books_active", 0))
            result.words_written_total = int(payload.get("words_written_total", 0))
            result.words_target_per_book = dict(payload.get("words_target_per_book", {}))
            result.completion_pct = dict(payload.get("completion_pct", {}))
            result.last_writing_session = dict(payload.get("last_writing_session", {}))
        return result

    result.books_active = int(os.environ.get("DF_168_MOCK_BOOKS_ACTIVE", "0"))
    result.words_written_total = int(os.environ.get("DF_168_MOCK_WORDS_TOTAL", "0"))
    result.words_target_per_book = _json_env_dict("DF_168_MOCK_TARGETS")
    result.completion_pct = _json_env_dict("DF_168_MOCK_COMPLETION")
    result.last_writing_session = _json_env_dict("DF_168_MOCK_LAST_SESSION")
    return result


def _json_env_dict(name: str) -> dict:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return value


def main() -> int:
    if not acquire_lock_with_identity():
        return 3

    try:
        pav = k17_pre_action_verification(["DF_DIR", "DF_ID", "LOCK_PARENT"])
        if not pav.get("ok"):
            return 3

        tracker = collect_tracker_output()
        payload = asdict(tracker)
        payload["pre_action_verification"] = pav

        rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        assert_no_decision_keywords(rendered)

        report_dir = DF_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        date_tag = datetime.now(timezone.utc).date().isoformat()
        report_path = report_dir / f"df-168-{date_tag}.json"
        report_path.write_text(rendered + "\n", encoding="utf-8")
        return 0
    except Exception as exc:
        error_payload = {
            "welle": "25",
            "df": "DF-168",
            "iso_timestamp": iso_now(),
            "source": "error",
            "error": exc.__class__.__name__,
            "message": str(exc),
        }
        try:
            assert_no_decision_keywords(error_payload)
            report_dir = DF_DIR / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            date_tag = datetime.now(timezone.utc).date().isoformat()
            report_path = report_dir / f"df-168-{date_tag}.json"
            report_path.write_text(
                json.dumps(error_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        return 3
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())