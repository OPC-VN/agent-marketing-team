# -*- coding: utf-8 -*-
"""Giọng đọc là CẤU HÌNH, không phải mã (voice-station-restructure DN10/DN11, TK3).

Ba cổng:
1. `campaign_cfg.gop` ghép `voice_profile` theo thứ tự campaign.md > channel.yml > brand.md > không khai,
   và ghi nguồn vào `voice_profile_source`.
2. `Resolve-VoiceProfile` (brand-paths.ps1): `-Profile` thắng cấu hình; không khai thì tên RỖNG (runner
   không truyền `--profile`, voice-studio dùng mặc định của trạm).
3. Mã repo không mang bảng series → giọng: không `pick-voice.ps1`, không tên giọng thật trong runner.
4. `voice.list_profiles/inventory`: hỏi `voice-studio profiles list --json`; lệnh chưa có thì lùi kho cũ.

Không mạng, không đăng, không chạm trạm thật.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = ROOT / "scripts" / "runners"
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
import campaign_cfg as CC  # noqa: E402
import studio_contract as SC  # noqa: E402
import voice as VOICE  # noqa: E402

PS = shutil.which("powershell") or shutil.which("pwsh")


# ── 1. campaign_cfg: thứ tự ghép ─────────────────────────────────────────────────────────

def _tram(tmp_path, *, channel_vp=None, campaign_vp=None, brand_md_vp=None, pool=None):
    kenh = tmp_path / "kenh-a"
    cd = kenh / "cd-1"
    cd.mkdir(parents=True)
    ch = ["schema: channel/1", "id: kenh-a", "brand:", "  site_name: X"]
    if channel_vp:
        ch.insert(2, f"voice_profile: {channel_vp}")
    (kenh / "channel.yml").write_text("\n".join(ch) + "\n", encoding="utf-8")
    if brand_md_vp:
        (kenh / "brand.md").write_text(
            f"---\nschema: brand/1\nchannel: kenh-a\nvoice_profile: {brand_md_vp}\n---\n", encoding="utf-8")
    rt = ["  label: X", "  runner: run-x.ps1"]
    if campaign_vp:
        rt.append(f"  voice_profile: {campaign_vp}")
    if pool:
        rt.append("  voice_pool: [" + ", ".join(pool) + "]")
    (cd / "campaign.md").write_text(
        "---\nschema: campaign/1\nid: cd-1\nchannel: kenh-a\nruntime:\n" + "\n".join(rt) + "\n---\n# x\n",
        encoding="utf-8")
    return cd


@pytest.mark.parametrize("kw,mong,nguon", [
    (dict(campaign_vp="gc", channel_vp="gk", brand_md_vp="gb"), "gc", "campaign.md: runtime.voice_profile"),
    (dict(channel_vp="gk", brand_md_vp="gb"), "gk", "channel.yml: voice_profile"),
    (dict(brand_md_vp="gb"), "gb", "brand.md: voice_profile"),
    (dict(), None, None),
])
def test_cfg_voice_profile_thu_tu_campaign_channel_brand(tmp_path, kw, mong, nguon):
    cfg = CC.gop(_tram(tmp_path, **kw))
    assert cfg.get("voice_profile") == mong
    assert cfg.get("voice_profile_source") == nguon


def test_cfg_voice_pool_di_qua_runtime(tmp_path):
    cfg = CC.gop(_tram(tmp_path, channel_vp="gk", pool=["g-mot", "g-hai"]))
    assert cfg["voice_pool"] == ["g-mot", "g-hai"] and cfg["voice_profile"] == "gk"


# ── 2. Resolve-VoiceProfile (PowerShell) ─────────────────────────────────────────────────

def _resolve(explicit, cfg_json):
    if not PS:
        pytest.skip("không có PowerShell")
    script = (
        "$ErrorActionPreference='Stop'; . '%s'; "
        "$cfg = '%s' | ConvertFrom-Json; "
        "$r = Resolve-VoiceProfile -Explicit '%s' -Cfg $cfg; "
        "Write-Output ('NAME=[' + $r.name + '] SRC=[' + $r.source + ']')"
        % (RUNNERS / "brand-paths.ps1", cfg_json, explicit))
    env = dict(os.environ, MARKETING_STUDIO_DATA=tempfile.gettempdir())
    p = subprocess.run([PS, "-NoProfile", "-NonInteractive", "-Command", script],
                       capture_output=True, text=True, timeout=90, env=env, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    return p.stdout.strip().splitlines()[-1]


def test_ps_tham_so_profile_thang_cau_hinh():
    out = _resolve("g-tay", json.dumps({"voice_profile": "g-cfg", "voice_profile_source": "campaign.md"}))
    assert out == "NAME=[g-tay] SRC=[tham so -Profile]"


def test_ps_cau_hinh_roi_den_nguon():
    out = _resolve("", json.dumps({"voice_profile": "g-cfg", "voice_profile_source": "channel.yml: voice_profile"}))
    assert out == "NAME=[g-cfg] SRC=[channel.yml: voice_profile]"


def test_ps_khong_khai_thi_ten_rong_khong_doan_giong():
    out = _resolve("", json.dumps({"label": "X"}))
    assert out.startswith("NAME=[] SRC=[khong khai")


# ── 3. mã repo không mang bảng series → giọng ────────────────────────────────────────────

def test_repo_khong_con_pick_voice_va_khong_goi_no():
    assert not (RUNNERS / "pick-voice.ps1").exists(), "bảng series → giọng là CẤU HÌNH, không nằm trong repo"
    for f in RUNNERS.glob("*.ps1"):
        code = "\n".join(ln for ln in f.read_text(encoding="utf-8-sig").splitlines()
                         if not ln.lstrip().startswith("#"))
        assert "pick-voice" not in code, f"{f.name} còn gọi pick-voice"


def test_runner_tin_co_che_do_chay_kho_ResolveOnly():
    for f in ("run-toptoday-hot.ps1", "run-weekly-news.ps1", "run-weekly-repo.ps1", "run-daily-truyen.ps1"):
        t = (RUNNERS / f).read_text(encoding="utf-8-sig")
        assert "$ResolveOnly" in t, f
    for f in ("run-toptoday-hot.ps1", "run-weekly-news.ps1", "run-weekly-repo.ps1"):
        assert "Resolve-VoiceProfile" in (RUNNERS / f).read_text(encoding="utf-8-sig"), f


def test_runner_truyen_thieu_Config_tu_sinh_tu_campaign_md_hoac_dung():
    """Khong bao gio am tham roi ve giong mac dinh kenh khi campaign co voice_pool (review Opus/Fable PS1)."""
    t = (RUNNERS / "run-daily-truyen.ps1").read_text(encoding="utf-8-sig")
    i_tu_sinh = t.index("campaign_cfg.py")
    i_doc_cfg = t.index("$cfg = $null")
    assert i_tu_sinh < i_doc_cfg, "tu sinh -Config phai TRUOC khi doc voice_pool"
    khoi = t[i_tu_sinh - 400:i_doc_cfg]
    assert khoi.count("exit 2") >= 2, "khong sinh duoc cau hinh -> exit != 0, khong chay tiep"
    assert "--campaign $Campaign" in khoi


# ── 4. voice.list_profiles / inventory ───────────────────────────────────────────────────

def test_list_profiles_doc_dong_json_cuoi(monkeypatch):
    payload = {"ok": True, "profiles": [
        {"name": unicodedata.normalize("NFD", "Giọng-A"), "kind": "tone", "markers": ["vui"],
         "default": True, "voice_dir": "x"}, "giong-b"]}
    monkeypatch.setattr(VOICE, "python_exe", lambda *a, **k: "/py")
    monkeypatch.setattr(SC, "call", lambda argv, **k: payload)
    ds = VOICE.list_profiles()
    assert [d["name"] for d in ds] == [unicodedata.normalize("NFC", "Giọng-A"), "giong-b"]
    names, nguon, kho = VOICE.inventory()
    assert nguon == "cli" and kho is None and "giong-b" in names


def test_lenh_chua_co_thi_lui_kho_cu_va_noi_ra(tmp_path, monkeypatch, capsys):
    kho = tmp_path / "voices"
    kho.mkdir()
    (kho / "giong-cu.wav").write_bytes(b"x")
    (kho / "_archive.wav").write_bytes(b"x")
    monkeypatch.setattr(VOICE, "python_exe", lambda *a, **k: "/py")

    def hong(argv, **k):
        raise SC.ContractError("profiles: lệnh lạ")
    monkeypatch.setattr(SC, "call", hong)
    monkeypatch.setattr(VOICE, "voices_dir", lambda *a, **k: kho)
    names, nguon, k2 = VOICE.inventory()
    assert nguon == "kho cũ" and names == {"giong-cu"} and k2 == kho
    assert "CẢNH BÁO" in capsys.readouterr().err


def test_khong_hoi_duoc_va_khong_co_kho_thi_none(monkeypatch):
    monkeypatch.setattr(VOICE, "python_exe", lambda *a, **k: (_ for _ in ()).throw(SC.StationMissing("x")))
    monkeypatch.setattr(VOICE, "voices_dir", lambda *a, **k: (_ for _ in ()).throw(SC.StationMissing("y")))
    assert VOICE.inventory() == (None, "không", None)
