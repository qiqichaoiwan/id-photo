#!/usr/bin/env python3
"""Download the HivisionIDPhotos model files required by the API.

The source repository is intentionally kept free of large binary weights. Each
download is restricted to a pinned URL, written atomically, and checked by
size and SHA-256 before it becomes visible to the application.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "hivision-core" / "hivision" / "creator" / "weights"

MODELS = {
    "hivision_modnet": {
        "url": "https://github.com/Zeyi-Lin/HivisionIDPhotos/releases/download/pretrained-model/hivision_modnet.onnx",
        "filename": "hivision_modnet.onnx",
        "size": 25_888_609,
        "sha256": "7e0cb9a2a841b426dd0daf1a788ec398dab059bc039041d62b15636c0783bc56",
    },
    "modnet_photographic_portrait_matting": {
        "url": "https://github.com/Zeyi-Lin/HivisionIDPhotos/releases/download/pretrained-model/modnet_photographic_portrait_matting.onnx",
        "filename": "modnet_photographic_portrait_matting.onnx",
        "size": 25_888_640,
        "sha256": "07c308cf0fc7e6e8b2065a12ed7fc07e1de8febb7dc7839d7b7f15dd66584df9",
    },
    "birefnet-v1-lite": {
        "url": "https://github.com/ZhengPeng7/BiRefNet/releases/download/v1/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx",
        "filename": "birefnet-v1-lite.onnx",
        "size": 224_005_088,
        "sha256": "5600024376f572a557870a5eb0afb1e5961636bef4e1e22132025467d0f03333",
    },
}


def verify(path: Path, spec: dict) -> bool:
    if not path.is_file() or path.stat().st_size != spec["size"]:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == spec["sha256"]


def download(name: str, spec: dict) -> None:
    target = WEIGHTS / spec["filename"]
    if verify(target, spec):
        print(f"已存在并通过校验：{target.name}")
        return
    WEIGHTS.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=WEIGHTS)
    temporary = Path(temporary_name)
    digest = hashlib.sha256()
    received = 0
    try:
        request = Request(spec["url"], headers={"User-Agent": "id-photo-backend-bootstrap/1"})
        with urlopen(request, timeout=60) as response, os.fdopen(fd, "wb") as stream:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                stream.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                print(f"\r{name}: {received / 1024 / 1024:.1f} MiB", end="", flush=True)
        print()
        if received != spec["size"] or digest.hexdigest() != spec["sha256"]:
            raise RuntimeError(f"{name} 下载后校验失败（大小或 SHA-256 不匹配）")
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
        print(f"已安装：{target}")
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", choices=[*MODELS, "all"], default=["all"])
    args = parser.parse_args(argv)
    selected = list(MODELS) if "all" in args.models else args.models
    for name in selected:
        download(name, MODELS[name])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
