from __future__ import annotations

import hashlib
import json
import platform
import sys

from experiment_utils import root


def build_fingerprint() -> dict[str, object]:
    payload: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
    }
    try:
        import torch

        payload.update(
            {
                "torch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count(),
                "cuda_device_name": (
                    torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""
                ),
            }
        )
    except Exception as exc:
        payload["torch_probe_error"] = type(exc).__name__
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    payload["environment_fingerprint_hash"] = digest
    return payload


def main() -> None:
    output = root / "artifacts" / "environment" / "fingerprint.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = build_fingerprint()
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Environment fingerprint: {payload['environment_fingerprint_hash']}")
    print(f"Artifact: {output.relative_to(root)}")


if __name__ == "__main__":
    main()
