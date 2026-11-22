# -*- coding: utf-8 -*-
"""Pipeline truyện không còn neo vào `<trạm giọng>/omnivoice` (voice-station-restructure TK3, DN3/DN4/DN11).

· `truyen_paths.layout`      : ghi theo CHIẾN DỊCH `<chiến dịch>/out|work|logs`; chưa có chiến dịch thì cây cũ / nháp.
· `truyen_paths.media_file`  : nhạc ở trạm giọng, hình ở trạm video; chưa dời thì lùi cây cũ + cảnh báo.
· `daily_truyen.use_campaign`: đặt đường ghi + đưa chiến dịch cho tiến trình con.
· `resume_once.dau_tu_lenh`  : dấu resume suy từ `--state`.

Không mạng, không chạm trạm thật (mọi biến trỏ vào thư mục tạm).
"""
import ast
import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / "scripts" / "runners" / "story"
sys.path.insert(0, str(STORY))
sys.path.insert(0, str(ROOT / "scripts" / "runners"))
import truyen_paths as TP  # noqa: E402

BIEN = ("VOICE_STATION", "VIDEO_STATION", "VIDEO_ROOT", "OMNIVOICE_DIR", "OMNIVOICE_PY",
        "TRUYEN_CAMPAIGN_DIR", "MARKETING_STUDIO_DATA", "MARKETING_STUDIO_HOME")


@pytest.fixture
def cay(tmp_path, monkeypatch):
    for b in BIEN:
        monkeypatch.delenv(b, raising=False)
    # Windows: `getenv` đọc thêm registry User — máy thật có VOICE_STATION/OMNIVOICE_DIR ở đó. Test chỉ nhìn môi trường.
    monkeypatch.setattr(TP, "getenv", lambda name, env=None, registry=True:
                        ((os.environ if env is None else env).get(name) or "").strip())
    kenh = tmp_path / "marketing" / "nghe-tien-truyen"
    cd = kenh / "phan-2"
    cd.mkdir(parents=True)
    (cd / "truyen-state.json").write_text("{}", encoding="utf-8")
    (kenh / "channel.yml").write_text(
        "schema: channel/1\nid: nghe-tien-truyen\nmedia:\n  music:\n    bgm: nhac-1.mp3\n    bgm_daily: nhac-2.mp3\n"
        "  video_kit:\n    background: nen.mp4\n    title_fire: shared/overlays/lua.mp4\n", encoding="utf-8")
    giong = tmp_path / "voice"
    video = tmp_path / "video"
    giong.mkdir()
    video.mkdir()
    return {"cd": cd, "giong": giong, "video": video, "tmp": tmp_path}


def _touch(p):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    return str(p)


def test_layout_theo_chien_dich(cay):
    lay = TP.layout(str(cay["cd"]))
    cd = str(cay["cd"])
    assert lay["mode"] == "campaign"
    assert lay["out"] == os.path.join(cd, "out") and lay["scratch"] == os.path.join(cd, "work")
    assert lay["logs"] == os.path.join(cd, "logs") and lay["work"] == os.path.join(cd, "work", "_work")


def test_layout_doc_env_TRUYEN_CAMPAIGN_DIR(cay, monkeypatch):
    monkeypatch.setenv("TRUYEN_CAMPAIGN_DIR", str(cay["cd"]))
    assert TP.layout()["out"] == os.path.join(str(cay["cd"]), "out")


def test_layout_khong_chien_dich_lui_cay_cu_co_canh_bao(cay, monkeypatch, capsys):
    eng = cay["giong"] / "omnivoice"
    (eng / "truyen-out").mkdir(parents=True)
    monkeypatch.setenv("VOICE_STATION", str(cay["giong"]))
    lay = TP.layout()
    assert lay["mode"] == "legacy" and lay["scratch"] == str(eng / "truyen-out")
    assert "cây cũ" in capsys.readouterr().err


def test_layout_khong_chien_dich_khong_cay_cu_thi_nhap_o_tram_giong(cay, monkeypatch):
    monkeypatch.setenv("VOICE_STATION", str(cay["giong"]))
    lay = TP.layout()
    assert lay["mode"] == "adhoc" and lay["scratch"] == str(cay["giong"] / "out" / "truyen")


def test_voice_station_khong_ghep_omnivoice_va_nhan_ten_cu(cay, monkeypatch):
    monkeypatch.setenv("OMNIVOICE_DIR", str(cay["giong"] / "omnivoice"))
    assert TP.voice_station() == str(cay["giong"])
    monkeypatch.setenv("VOICE_STATION", str(cay["tmp"] / "khac"))
    assert TP.voice_station() == str(cay["tmp"] / "khac")        # tên mới thắng tên cũ


def test_media_nhac_o_tram_giong_hinh_o_tram_video(cay, monkeypatch):
    monkeypatch.setenv("VOICE_STATION", str(cay["giong"]))
    monkeypatch.setenv("VIDEO_STATION", str(cay["video"]))
    cd = str(cay["cd"])
    nhac = _touch(cay["giong"] / "music" / "channels" / "nghe-tien-truyen" / "nhac-1.mp3")
    nen = _touch(cay["video"] / "assets" / "channels" / "nghe-tien-truyen" / "nen.mp4")
    lua = _touch(cay["video"] / "assets" / "shared" / "overlays" / "lua.mp4")
    assert TP.media_file("music", "bgm", "cu.mp3", campaign=cd) == nhac
    assert TP.media_file("video_kit", "background", "cu.mp4", campaign=cd) == nen
    assert TP.media_file("video_kit", "title_fire", "cu.mp4", campaign=cd) == lua   # `shared/` → assets/shared


def test_media_chua_doi_tram_lui_ten_cu_va_canh_bao(cay, monkeypatch, capsys):
    monkeypatch.setenv("VOICE_STATION", str(cay["giong"]))
    cu = _touch(cay["giong"] / "omnivoice" / "assets" / "Nhạc nền cũ.mp3")
    assert TP.media_file("music", "bgm", "Nhạc nền cũ.mp3", campaign=str(cay["cd"])) == cu
    assert "dùng bản cũ" in capsys.readouterr().err
    assert TP.media_file("music", "outro", "khong-co.mp3", campaign=str(cay["cd"])) == ""


def test_is_default_voice_nhan_ten_cu_co_dau():
    for ten in ("giong-tien-hiep", "Giọng tiên hiệp", "giong tien hiep"):
        assert TP.is_default_voice(ten)
    assert not TP.is_default_voice("giong-khac")


def test_title_font_uu_tien_tram_video(cay, monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", str(cay["video"]))
    f = _touch(cay["video"] / "assets" / "shared" / "fonts" / "title.ttf")
    assert TP.title_font() == f


def test_daily_truyen_use_campaign_dat_duong_va_env(cay, monkeypatch):
    monkeypatch.setenv("VOICE_STATION", str(cay["giong"]))
    monkeypatch.setenv("VIDEO_STATION", str(cay["video"]))
    monkeypatch.setenv("TRUYEN_CAMPAIGN_DIR", "")        # `use_campaign` ghi nó vào os.environ; teardown trả lại
    dt = importlib.import_module("daily_truyen")
    lay = dt.use_campaign(str(cay["cd"] / "truyen-state.json"))
    assert dt.OUT_DIR == os.path.join(str(cay["cd"]), "out") and dt.OUT_ROOT == os.path.join(str(cay["cd"]), "work")
    assert dt.LOGDIR == os.path.join(str(cay["cd"]), "logs") and lay["mode"] == "campaign"
    assert os.environ["TRUYEN_CAMPAIGN_DIR"] == str(cay["cd"]) and dt.ENV["TRUYEN_CAMPAIGN_DIR"] == str(cay["cd"])


def test_resume_once_suy_dau_tu_state(cay):
    ro = importlib.import_module("resume_once")
    cmd = ["py", "-u", "daily_truyen.py", "--state", str(cay["cd"] / "truyen-state.json")]
    assert ro.dau_tu_lenh(cmd) == os.path.join(str(cay["cd"]), "work", "_resume.json")
    assert ro.dau_tu_lenh(["py", "x.py"]) is None


def test_runner_truyen_khong_con_ghi_cung_omnivoice_hay_OMNIVOICE_DIR_bat_buoc():
    for f in ("daily_truyen.py", "audio_truyen.py", "make_video.py", "read_story.py", "heal_agent.py",
              "truyen_publish.py"):
        cay_ast = ast.parse((STORY / f).read_text(encoding="utf-8"))
        ten = {n.id for n in ast.walk(cay_ast) if isinstance(n, ast.Name)}
        goi = {n.func.attr for n in ast.walk(cay_ast)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        chuoi = {n.value for n in ast.walk(cay_ast) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert "ENGINE" not in ten and "engine_dir" not in goi, f
        assert "truyen-out" not in chuoi and "omnivoice" not in chuoi, f


def test_parse_media_khoi_thut_le_co_chu_thich_khong_can_pyyaml():
    text = ("id: k\nvoice_profile: g\nmedia:\n  music:\n    bgm: a.mp3   # cũ: Nhạc.mp3\n    outro: \"b.mp3\"\n"
            "  video_kit:\n    title_fire: shared/overlays/x.mp4\n# chú thích\nplatforms:\n  - channel: youtube\n"
            "    handle: z\n")
    assert TP.parse_media(text) == {"music": {"bgm": "a.mp3", "outro": "b.mp3"},
                                    "video_kit": {"title_fire": "shared/overlays/x.mp4"}}
    assert TP.parse_media("id: k\nplatforms:\n  - channel: x\n") == {}
