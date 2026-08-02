"""Manage Netscape cookies file for yt-dlp YouTube fallback."""

from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_LOGIN_COOKIE = "LOGIN_INFO"
_SESSION_MARKERS = frozenset({"SID", "__Secure-1PSID", "SAPISID"})


def get_cookies_path() -> Path:
    """Resolve cookies file path from env or default ./cookies.txt."""
    raw = os.getenv("COOKIES_FILE", "cookies.txt")
    return Path(raw).expanduser().resolve()


def cookies_exist() -> bool:
    path = get_cookies_path()
    return path.is_file() and path.stat().st_size > 0


def _normalize_expiry(raw: int) -> int:
    """Netscape expiry is Unix seconds; some exports use milliseconds."""
    if raw > 10**12:
        return raw // 1000
    return raw


def _is_youtube_domain(domain: str) -> bool:
    domain = domain.lstrip(".").lower()
    return domain == "youtube.com" or domain.endswith(".youtube.com")


def _parse_cookie_lines(text: str) -> list[dict]:
    """Parse Netscape HTTP Cookie File lines into dicts."""
    cookies: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            # Keep #HttpOnly_ prefix support
            if line.startswith("#HttpOnly_"):
                line = line[len("#HttpOnly_") :]
            else:
                continue

        parts = line.split("\t")
        if len(parts) < 7:
            continue

        domain, _flag, path, _secure, expiry_s, name, value = parts[:7]
        try:
            expiry = _normalize_expiry(int(expiry_s))
        except ValueError:
            continue

        cookies.append(
            {
                "domain": domain,
                "path": path,
                "expiry": expiry,
                "name": name,
                "value": value,
            }
        )
    return cookies


def is_cookies_fresh(now: float | None = None) -> tuple[bool, str]:
    """
    Check that cookies file exists and YouTube login cookies are valid.

    Returns:
        (ok, reason) where reason is a short machine-readable code.
    """
    path = get_cookies_path()
    if not path.is_file():
        return False, "missing"
    if path.stat().st_size == 0:
        return False, "empty"

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Cannot read cookies file %s: %s", path, exc)
        return False, "unreadable"

    cookies = _parse_cookie_lines(text)
    if not cookies:
        return False, "invalid_format"

    yt_cookies = [c for c in cookies if _is_youtube_domain(c["domain"])]
    if not yt_cookies:
        return False, "no_youtube_cookies"

    ts = int(now if now is not None else time.time())

    by_name = {c["name"]: c for c in yt_cookies}

    login = by_name.get(_LOGIN_COOKIE)
    if login is None:
        return False, "no_login_info"

    exp = login["expiry"]
    if exp > 0 and exp < ts:
        return False, "login_expired"

    has_session = False
    for name in _SESSION_MARKERS:
        c = by_name.get(name)
        if c is None:
            continue
        exp = c["expiry"]
        if exp == 0 or exp >= ts:
            has_session = True
            break
        # expired marker — keep looking for another

    if not has_session:
        # All session markers missing or expired
        any_marker = any(n in by_name for n in _SESSION_MARKERS)
        if not any_marker:
            return False, "no_session_cookies"
        return False, "session_expired"

    return True, "ok"


def validate_cookies_content(content: str | bytes) -> tuple[bool, str]:
    """Validate raw cookies content without writing to disk."""
    if isinstance(content, bytes):
        text = content.decode("utf-8", errors="replace")
    else:
        text = content

    if not text.strip():
        return False, "empty"

    cookies = _parse_cookie_lines(text)
    if not cookies:
        return False, "invalid_format"

    yt = [c for c in cookies if _is_youtube_domain(c["domain"])]
    if not yt:
        return False, "no_youtube_cookies"

    names = {c["name"] for c in yt}
    if _LOGIN_COOKIE not in names:
        return False, "no_login_info"
    if not names & _SESSION_MARKERS:
        return False, "no_session_cookies"

    return True, "ok"


def save_cookies(content: str | bytes) -> tuple[bool, str]:
    """
    Validate and atomically write cookies file.

    Returns:
        (ok, reason) — on success reason is from is_cookies_fresh after write.
    """
    ok, reason = validate_cookies_content(content)
    if not ok:
        return False, reason

    if isinstance(content, bytes):
        data = content
    else:
        data = content.encode("utf-8")

    path = get_cookies_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write via temp + copy so bind-mounted cookies.txt in Docker stays valid
    # (os.replace onto a file mount can fail with EXDEV / break the mount).
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=".cookies_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())
            with open(tmp_name, "rb") as src, open(path, "wb") as dst:
                dst.write(src.read())
                dst.flush()
                os.fsync(dst.fileno())
        finally:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
    except OSError as exc:
        logger.exception("Failed to save cookies to %s", path)
        return False, f"write_error: {exc}"

    logger.info("Cookies saved to %s (%d bytes)", path, len(data))
    return is_cookies_fresh()


def reason_to_user_message(reason: str) -> str:
    """Human-readable Russian message for admin about cookie status."""
    mapping = {
        "missing": "Файл cookies отсутствует.",
        "empty": "Файл cookies пустой.",
        "unreadable": "Не удалось прочитать файл cookies.",
        "invalid_format": "Неверный формат cookies (ожидается Netscape cookies.txt).",
        "no_youtube_cookies": "В файле нет cookies для youtube.com.",
        "no_login_info": "Нет cookie LOGIN_INFO (нужна залогиненная сессия YouTube).",
        "login_expired": "Cookie LOGIN_INFO просрочен.",
        "no_session_cookies": "Нет сессионных cookies (SID / __Secure-1PSID / SAPISID).",
        "session_expired": "Сессионные cookies просрочены.",
        "ok": "Cookies в порядке.",
    }
    return mapping.get(reason, f"Проблема с cookies: {reason}")
