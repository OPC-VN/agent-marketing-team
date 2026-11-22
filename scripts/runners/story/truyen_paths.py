# -*- coding: utf-8 -*-
"""truyen_paths.py — MỘT chỗ phân giải đường cho pipeline truyện, chạy được Windows + macOS.

Mọi khác biệt giữa hai máy của pipeline truyện gom về đây (runbook PORTING-WINDOWS-MACOS,
nguyên tắc 1). Các script khác chỉ gọi hàm, không tự ghép `Scripts\\python.exe` hay
`C:\\...` nữa.

Ranh giới ba trạm (voice-station-restructure, DN11): NỘI DUNG + cấu hình kênh + log chạy ở
trạm marketing; mọi thứ HÌNH (nền, logo, lửa tiêu đề, font) ở trạm video; mọi thứ ÂM THANH
(giọng, nhạc) ở trạm giọng. Pipeline truyện KHÔNG còn neo vào `<trạm giọng>/omnivoice`.

    layout()          nơi ghi của MỘT chiến dịch: `<chiến dịch>/out|work|logs` (chiến dịch =
                      thư mục chứa `truyen-state.json`, truyền qua env TRUYEN_CAMPAIGN_DIR).
                      Chạy tay không có chiến dịch ⇒ cây cũ `<trạm giọng>/omnivoice/truyen-out`
                      nếu còn, không thì `<trạm giọng>/out/truyen` — kèm cảnh báo.
    voice_station()   gốc trạm giọng: VOICE_STATION → (tên cũ) thư mục CHA của OMNIVOICE_DIR →
                      `studio_paths.voice_station()` → DỪNG, nêu tên biến.
    video_station()   gốc trạm video: VIDEO_STATION → VIDEO_ROOT → studio_paths → "".
    media_file()      nhạc/intro/outro: `<trạm giọng>/music/channels/<kênh>/` ; hình/logo/lửa:
                      `<trạm video>/assets/channels/<kênh>/` (`shared/…` → `assets/shared/…`);
                      tên khai ở `channel.yml: media`. Chưa dời trạm (TK5) ⇒ lùi về
                      `<trạm giọng>/omnivoice/assets/<tên cũ>` + cảnh báo.
    engine_dir()      [LEGACY — chỉ để đọc cây cũ] OMNIVOICE_DIR → <VOICE_STATION>/omnivoice →
                      ... → DỪNG. Không còn script nào BẮT BUỘC nó.
    venv_python()     python của venv torch: OMNIVOICE_PY → <engine>/.venv/{Scripts,bin}/python*
                      → `station.json: venv` của trạm giọng → runtime của OpcOS → `.venv` của repo
                      anh em `agent-video-studio` rồi `agent-voice-studio` → chính interpreter
                      đang chạy (lượt đêm vốn đã chạy bằng venv đó).
    publish_python()  python cho bước đăng (cần google-api-python-client):
                      TRUYEN_PUBLISH_PY → python / python3 / py -3 trên PATH mà import được
                      googleapiclient và ≥ 3.10 → interpreter đang chạy.
    title_font()      font tiêu đề (phải có dấu tiếng Việt): TRUYEN_FONT → <trạm video>/assets/
                      shared/fonts/title.ttf → <engine>/assets/fonts/title.ttf (cũ) → font hệ
                      thống theo OS → DỪNG, nói đặt TRUYEN_FONT.
    upload_engine_dir() thư mục chứa youtube_upload.py: `scripts/runners` của repo (cha của
                      thư mục này) → <MARKETING_STUDIO_DATA>/engine → <trạm chứa file này>/engine
                      (bản cũ; chỉ nhận thư mục CÓ youtube_upload.py). CHỈ trả đường — không
                      đọc token/secret nào.

Trên Windows, biến vừa `setx` không tới tiến trình đang chạy: nếu biến tiến trình rỗng thì
đọc thêm registry User (giống Get-EnvVar của engine/brand-paths.ps1). Trên macOS biến phải
khai trong plist launchd.
"""
import os
import shutil
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
# `<repo>/scripts/lib` khi file này nằm ở `<repo>/scripts/runners/story/`. Bản cũ trong trạm
# không có repo cạnh bên -> các tầng dùng studio_paths tự bỏ qua.
_LIB = os.path.join(os.path.dirname(os.path.dirname(HERE)), "lib")


def _sp():
    """`studio_paths` của repo, hoặc None (bản cũ trong trạm / thiếu phụ thuộc)."""
    if not os.path.isfile(os.path.join(_LIB, "studio_paths.py")):
        return None
    if _LIB not in sys.path:
        sys.path.insert(0, _LIB)
    try:
        import studio_paths
        return studio_paths
    except Exception:  # noqa: BLE001 — thiếu pyyaml trong venv giọng thì bỏ tầng này, không chết
        return None


def _expand(p):
    return os.path.abspath(os.path.expanduser(os.path.expandvars(str(p))))


def getenv(name, env=None, registry=True):
    """Biến tiến trình; rỗng thì (chỉ Windows) đọc registry HKCU\\Environment."""
    env = os.environ if env is None else env
    v = (env.get(name) or "").strip()
    if v or not registry or sys.platform != "win32":
        return v
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            val, _ = winreg.QueryValueEx(k, name)
        return str(val or "").strip()
    except OSError:
        return ""


TOKEN_VAR_TRUYEN = "YT_TOKEN_PATH__NGHE_TIEN_TRUYEN"


def token_truyen(env=None, registry=True):
    """ĐƯỜNG token kênh truyện (không mở file): `YT_TOKEN_PATH__NGHE_TIEN_TRUYEN` (tiến trình →
    registry User chỉ trên Windows) THẮNG `YT_TOKEN_PATH` chung (chỉ tiến trình) → "".

    Vì sao biến riêng kênh phải thắng (P3-12): env plist/tác vụ truyện có thể mang
    `YT_TOKEN_PATH` của kênh KHÁC (kênh tin) — chạy tay `truyen_publish.py` trong env đó mà
    ưu tiên biến chung là đăng nhầm kênh. `YT_TOKEN_PATH` chung KHÔNG đọc registry: trên
    Windows registry giữ token của kênh tin, không phải kênh truyện."""
    env_ = os.environ if env is None else env
    v = getenv(TOKEN_VAR_TRUYEN, env, registry) or (env_.get("YT_TOKEN_PATH") or "").strip()
    return os.path.expanduser(v) if v else ""


def engine_dir(env=None, registry=True, sp=None):
    eng = getenv("OMNIVOICE_DIR", env, registry)
    if eng:
        return _expand(eng)
    st = getenv("VOICE_STATION", env, registry)
    if st:
        return os.path.join(_expand(st), "omnivoice")
    # Tầng repo: studio.local.json / repo anh em `agent-voice-studio` cùng thư mục cha. Chỉ
    # khi người gọi dùng môi trường THẬT — test truyền `env` giả thì không được rò ra máy thật.
    SP = sp if sp is not None else (_sp() if env is None else None)
    if SP is not None:
        try:
            goc = SP.voice_station()
        except Exception:  # noqa: BLE001
            goc = None
        if goc:
            return os.path.join(str(goc), "omnivoice")
    raise SystemExit("truyen_paths: không biết trạm giọng ở đâu — đặt VOICE_STATION (gốc trạm "
                     "giọng, vd <repo agent-voice-studio>/workspaces) hoặc OMNIVOICE_DIR (thư mục "
                     "engine của trạm đó), ở biến môi trường hoặc <repo>/.env (embedded).")


def _warn(msg):
    sys.stderr.write("[truyen_paths] WARN: " + msg + "\n")
    sys.stderr.flush()


# ── ba trạm: giọng · video · chiến dịch ─────────────────────────────────────────────────

CHANNEL_ID = "nghe-tien-truyen"          # tên thư mục kênh trong trạm marketing
ENV_CAMPAIGN = "TRUYEN_CAMPAIGN_DIR"     # thư mục chiến dịch (chứa truyen-state.json)
DEFAULT_VOICE = "giong-tien-hiep"        # profile giọng của kênh; tên cũ có dấu chỉ còn để nhận ra
_TEN_CU_GIONG_MAC_DINH = ("giọng tiên hiệp", "giong tien hiep", DEFAULT_VOICE)


def is_default_voice(name):
    """Giọng mặc định của kênh? (nhận cả tên cũ có dấu). Quyết định hậu tố cache/tên file."""
    s = unicodedata.normalize("NFC", str(name or "")).strip().lower()
    return s in {unicodedata.normalize("NFC", x) for x in _TEN_CU_GIONG_MAC_DINH}


def voice_station(env=None, registry=True, sp=None):
    """Gốc TRẠM GIỌNG: VOICE_STATION → (tên cũ) thư mục CHA của OMNIVOICE_DIR → studio_paths →
    DỪNG. Không có phép ghép `omnivoice` nào ở đây."""
    st = getenv("VOICE_STATION", env, registry)
    if st:
        return _expand(st)
    cu = getenv("OMNIVOICE_DIR", env, registry)
    if cu:
        return os.path.dirname(_expand(cu))      # tên cũ trỏ ENGINE; trạm = thư mục cha
    SP = sp if sp is not None else (_sp() if env is None else None)
    if SP is not None:
        try:
            goc = SP.voice_station()
        except Exception:  # noqa: BLE001
            goc = None
        if goc:
            return str(goc)
    raise SystemExit("truyen_paths: không biết trạm giọng ở đâu — đặt VOICE_STATION (gốc trạm "
                     "giọng, vd <repo agent-voice-studio>/workspaces), ở biến môi trường hoặc "
                     "<repo>/.env (embedded).")


def video_station(env=None, registry=True, sp=None):
    """Gốc TRẠM VIDEO, hoặc "" khi chưa biết (nền/logo/lửa sẽ lùi về cây cũ trong trạm giọng)."""
    st = getenv("VIDEO_STATION", env, registry) or getenv("VIDEO_ROOT", env, registry)
    if st:
        return _expand(st)
    SP = sp if sp is not None else (_sp() if env is None else None)
    if SP is not None:
        try:
            goc = SP.video_station()
        except Exception:  # noqa: BLE001
            goc = None
        if goc:
            return str(goc)
    return ""


def _legacy_engine(env=None, registry=True, sp=None):
    """Thư mục engine CŨ (`<trạm giọng>/omnivoice`) nếu còn trên đĩa, không thì ""."""
    try:
        e = engine_dir(env, registry, sp)
    except SystemExit:
        return ""
    return e if os.path.isdir(e) else ""


def layout(campaign=None, env=None, registry=True, sp=None):
    """Nơi GHI của pipeline truyện -> dict {mode, campaign, out, scratch, work, logs}.

    · `out`     thành phẩm (video "PNTT a-b.mp4")             — `<chiến dịch>/out`
    · `scratch` gốc cache chương + dấu resume; sweep dọn nó   — `<chiến dịch>/work`
    · `work`    thư mục dựng của lượt này (trong `scratch`)   — `<chiến dịch>/work/_work`
    · `logs`    log lượt chạy                                 — `<chiến dịch>/logs`

    Chiến dịch = `campaign` (tham số) hoặc env TRUYEN_CAMPAIGN_DIR (do runner/daily_truyen đặt).
    KHÔNG có chiến dịch (chạy tay một script lẻ) ⇒ cây cũ `<trạm giọng>/omnivoice/truyen-out` nếu
    còn (trạm chưa dời), không thì `<trạm giọng>/out/truyen`; cả hai đều kèm cảnh báo."""
    c = campaign or getenv(ENV_CAMPAIGN, env, False)
    if c:
        c = _expand(c)
        return {"mode": "campaign", "campaign": c, "out": os.path.join(c, "out"),
                "scratch": os.path.join(c, "work"), "work": os.path.join(c, "work", "_work"),
                "logs": os.path.join(c, "logs")}
    eng = _legacy_engine(env, registry, sp)
    if eng and os.path.isdir(os.path.join(eng, "truyen-out")):
        root = os.path.join(eng, "truyen-out")
        _warn(f"không có chiến dịch ({ENV_CAMPAIGN}) — ghi vào cây cũ {root}. Chạy qua "
              f"run-daily-truyen.ps1 / --state <chiến dịch>/truyen-state.json để ghi đúng chỗ.")
        return {"mode": "legacy", "campaign": "", "out": os.path.join(root, "out"),
                "scratch": root, "work": os.path.join(root, "_work"),
                "logs": os.path.join(root, "daily-logs")}
    root = os.path.join(voice_station(env, registry, sp), "out", "truyen")
    _warn(f"không có chiến dịch ({ENV_CAMPAIGN}) — ghi nháp vào {root}.")
    return {"mode": "adhoc", "campaign": "", "out": os.path.join(root, "out"),
            "scratch": root, "work": os.path.join(root, "_work"), "logs": os.path.join(root, "logs")}


def parse_media(text):
    """Khối `media:` của channel.yml -> {nhóm: {khoá: tên file}}. CHỈ kiểu khối thụt lề hai cấp
    (`media:` → `music:` → `bgm: file.mp3`), giá trị chuỗi, `# chú thích` cuối dòng bị bỏ. Không dùng
    PyYAML: venv giọng không bắt buộc có nó (cổng `runner_deps`), và khối này đơn giản có chủ đích."""
    out, trong, nhom = {}, False, None
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if not raw[0].isspace():                 # khoá cấp gốc: đang ở `media:` hay không
            trong, nhom = s.startswith("media:"), None
            continue
        if not trong:
            continue
        khoa, _, val = s.partition(":")
        val = val.split(" #")[0].strip().strip("\"'")
        if not val:
            nhom = khoa.strip()
            out[nhom] = {}
        elif nhom is not None:
            out[nhom][khoa.strip()] = val
    return out


def _channel_media(campaign, env=None):
    """-> (channel_id, khối `media:` của channel.yml) — {} khi không có/không đọc được."""
    cid = CHANNEL_ID
    media = {}
    if campaign:
        kenh = os.path.dirname(os.path.abspath(campaign))
        cid = os.path.basename(kenh) or CHANNEL_ID
        f = os.path.join(kenh, "channel.yml")
        if os.path.isfile(f):
            try:
                with open(f, encoding="utf-8") as fh:
                    media = parse_media(fh.read())
            except (OSError, UnicodeError):
                media = {}
    return cid, media


def media_file(kind, key, legacy_name, env=None, registry=True, sp=None, campaign=None):
    """Đường file media của kênh -> str, hoặc "" khi không đâu có.

    kind="music"     → `<trạm giọng>/music/channels/<kênh>/<tên>`           (DN4)
    kind="video_kit" → `<trạm video>/assets/channels/<kênh>/<tên>`; tên bắt đầu `shared/` →
                       `<trạm video>/assets/shared/…`
    `<tên>` lấy từ `channel.yml: media.<kind>.<key>`; không khai thì dùng ASCII mặc định
    `<key>.<ext của legacy_name>`. Đường mới chưa có (trạm chưa dời — TK5) ⇒ lùi về
    `<trạm giọng>/omnivoice/assets/<legacy_name>` kèm cảnh báo."""
    campaign = campaign or getenv(ENV_CAMPAIGN, env, False)
    cid, media = _channel_media(campaign, env)
    khai = (media.get(kind) or {}) if isinstance(media.get(kind), dict) else {}
    ten = str(khai.get(key) or (key + os.path.splitext(legacy_name)[1])).strip()
    cands = []
    if kind == "music":
        try:
            cands.append(os.path.join(voice_station(env, registry, sp), "music", "channels", cid, ten))
        except SystemExit:
            pass
    else:
        vs = video_station(env, registry, sp)
        if vs:
            if ten.startswith("shared/"):
                cands.append(os.path.join(vs, "assets", *ten.split("/")))
            else:
                cands.append(os.path.join(vs, "assets", "channels", cid, *ten.split("/")))
    for c in cands:
        if os.path.isfile(c):
            return c
    eng = _legacy_engine(env, registry, sp)
    if eng:
        cu = os.path.join(eng, "assets", legacy_name)
        if os.path.isfile(cu):
            _warn(f"{kind}/{key}: chưa có {cands[0] if cands else ten} — dùng bản cũ {cu} "
                  f"(trạm chưa dời; sau khi dời thì file nằm ở đường mới).")
            return cu
    return ""


def available_profiles(env=None, registry=True, sp=None):
    """Tên profile giọng CÓ THẬT (qua `voice-studio profiles list --json`), hoặc None khi không
    hỏi được (lệnh chưa có / trạm chưa sẵn). Không đọc thư mục kho giọng."""
    SP = sp if sp is not None else (_sp() if env is None else None)
    if SP is None:
        return None
    try:
        import voice
        return voice.profile_names()
    except Exception:  # noqa: BLE001 — danh sách chỉ để lọc pool; hỏng thì tin cấu hình
        return None


def _venv_candidates(engine):
    v = os.path.join(engine, ".venv")
    return [os.path.join(v, "Scripts", "python.exe"),   # Windows
            os.path.join(v, "bin", "python3"),          # macOS / Linux
            os.path.join(v, "bin", "python")]


def _station_venv(env, registry, sp):
    """Ứng viên python theo `station.json: venv` của trạm giọng, rồi runtime của OpcOS."""
    out = []
    try:
        goc = voice_station(env, registry, sp)
    except SystemExit:
        goc = ""
    if goc:
        try:
            import json
            with open(os.path.join(goc, "station.json"), encoding="utf-8") as fh:
                khai = str((json.load(fh) or {}).get("venv") or "").strip()
        except (OSError, ValueError, AttributeError):
            khai = ""
        if khai:
            v = khai if os.path.isabs(khai) else os.path.join(goc, khai)
            out += [os.path.join(v, "Scripts", "python.exe"), os.path.join(v, "bin", "python3"),
                    os.path.join(v, "bin", "python")]
    SP = sp if sp is not None else (_sp() if env is None else None)
    if SP is not None:
        try:
            rt = SP.runtime_resource("venvs", SP.REPO_GIONG, "omnivoice")
        except Exception:  # noqa: BLE001
            rt = None
        if rt:
            out += [os.path.join(str(rt), "Scripts", "python.exe"),
                    os.path.join(str(rt), "bin", "python3"), os.path.join(str(rt), "bin", "python")]
    return out


def venv_python(engine=None, env=None, sp=None):
    override = (os.environ if env is None else env).get("OMNIVOICE_PY")
    if override:
        return _expand(override)
    # Engine nêu TƯỜNG MINH (tham số, hoặc biến OMNIVOICE_DIR — test sandbox đặt nó) thắng trước, như
    # bản cũ; rồi `station.json: venv` / runtime của OpcOS (cùng thứ tự `lib/voice.py`); rồi venv trong
    # engine CŨ `<trạm giọng>/omnivoice/.venv` nếu còn trên đĩa (trạm đã dời thì nấc này tự vắng).
    nguoi_dung = engine or (_legacy_engine(env, env is None, sp) if getenv("OMNIVOICE_DIR", env, env is None) else "")
    for c in (_venv_candidates(nguoi_dung) if nguoi_dung else []):
        if os.path.isfile(c):
            return c
    for c in _station_venv(env, env is None, sp):
        if os.path.isfile(c):
            return c
    cu = _legacy_engine(env, env is None, sp)
    for c in (_venv_candidates(cu) if cu else []):
        if os.path.isfile(c):
            return c
    # `.venv` của repo anh em (bố cục "giọng cài chung venv video" — cùng thứ tự với
    # `scripts/lib/voice.py: python_exe`).
    SP = sp if sp is not None else (_sp() if env is None else None)
    if SP is not None:
        for ten in ("agent-video-studio", "agent-voice-studio"):
            try:
                r = SP.repo_anh_em(ten)
            except Exception:  # noqa: BLE001
                r = None
            if r:
                for c in _venv_candidates(str(r)):
                    if os.path.isfile(c):
                        return c
    return sys.executable


def _probe(argv, timeout=60):
    """Ứng viên chạy được, ≥ 3.10, có googleapiclient? (Windows: python3 có thể là stub Store.)"""
    try:
        r = subprocess.run(argv + ["-c", "import sys, googleapiclient; "
                                         "sys.exit(0 if sys.version_info >= (3, 10) else 1)"],
                           capture_output=True, timeout=timeout)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def publish_python(env=None, probe=_probe):
    """-> argv tiền tố (list) để chạy truyen_publish.py."""
    override = (os.environ if env is None else env).get("TRUYEN_PUBLISH_PY")
    if override:
        return [_expand(override)]
    cands = []
    for name in ("python", "python3"):
        exe = shutil.which(name)
        if exe and [exe] not in cands:
            cands.append([exe])
    py = shutil.which("py")
    if py:
        cands.append([py, "-3"])
    for argv in cands:
        if probe(argv):
            return argv
    return [sys.executable]


def _system_fonts(env=None):
    env = os.environ if env is None else env
    if sys.platform == "win32":
        windir = env.get("WINDIR") or env.get("SystemRoot") or ""
        return [os.path.join(windir, "Fonts", "arialbd.ttf")] if windir else []
    if sys.platform == "darwin":
        return ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf"]
    return ["/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def title_font(engine=None, env=None, system_fonts=None):
    """Font tiêu đề (có dấu tiếng Việt). Thứ tự: TRUYEN_FONT → `<trạm video>/assets/shared/fonts/
    title.ttf` → (cũ) `<engine>/assets/fonts/title.ttf` → font hệ thống. `engine` có thể None."""
    env = os.environ if env is None else env
    f = env.get("TRUYEN_FONT")
    if f:
        f = _expand(f)
        if os.path.isfile(f):
            return f
        raise SystemExit(f"truyen_paths: TRUYEN_FONT trỏ tới file không có: {f}")
    cands = []
    vs = video_station(None) if env is os.environ else video_station(env, registry=False)
    if vs:
        cands.append(os.path.join(vs, "assets", "shared", "fonts", "title.ttf"))
    if engine:
        cands.append(os.path.join(engine, "assets", "fonts", "title.ttf"))
    cands += _system_fonts(env) if system_fonts is None else system_fonts
    for c in cands:
        if os.path.isfile(c):
            return c
    raise SystemExit("truyen_paths: không tìm thấy font tiêu đề (cần font có dấu tiếng Việt). "
                     "Đặt TRUYEN_FONT trỏ tới một .ttf, hoặc đặt vào "
                     "<trạm video>/assets/shared/fonts/title.ttf. Đã thử: " + " | ".join(cands))


# `brew install ffmpeg-full` là keg-only: KHÔNG link vào /opt/homebrew/bin. Bản core ở đó (nếu
# có) thiếu drawtext/libass (P0-9), nên keg phải thắng PATH — nếu không, máy có cả hai bản dựng
# video bằng bản thiếu bộ lọc.
_KEG_FFMPEG_FULL = ("/opt/homebrew/opt/ffmpeg-full/bin", "/usr/local/opt/ffmpeg-full/bin")


def ff_exe(name, env=None, registry=True, platform=None, is_file=os.path.isfile,
           which=shutil.which):
    """`ffmpeg`/`ffprobe` mà pipeline truyện gọi: FFMPEG_DIR → (macOS) keg `ffmpeg-full` →
    PATH → tên trần (lỗi nổ ở chỗ gọi). `doctor` kiểm bộ lọc của ĐÚNG file này."""
    platform = platform or sys.platform
    duoi = ".exe" if platform == "win32" else ""
    thu = []
    d = getenv("FFMPEG_DIR", env, registry)
    if d:
        thu.append(_expand(d))
    if platform == "darwin":
        thu += list(_KEG_FFMPEG_FULL)
    for x in thu:
        p = os.path.join(x, name + duoi)
        if is_file(p):
            return p
    return which(name) or name


def upload_engine_dir(env=None, registry=True, home=None, here=None):
    cands = [os.path.normpath(os.path.join(here or HERE, ".."))]      # repo: scripts/runners
    data = getenv("MARKETING_STUDIO_DATA", env, registry)
    if data:
        cands.append(os.path.join(_expand(data), "engine"))
    cands.append(os.path.normpath(os.path.join(here or HERE, "..", "engine")))
    for c in cands:
        if os.path.isfile(os.path.join(c, "youtube_upload.py")):
            return c
    return cands[0]      # không có ở đâu: trả ứng viên đầu, import sẽ nổ nói rõ thiếu module
