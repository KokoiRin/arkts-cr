"""Lightweight path-based risk hints for review triage.

The hints are deliberately conservative labels, not automated judgements. They
help reviewers notice files that usually deserve a second look.
"""

from __future__ import annotations

from pathlib import PurePosixPath


LOCKFILES = {
    "Cargo.lock",
    "Gemfile.lock",
    "Podfile.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}

CONFIG_NAMES = {
    ".babelrc",
    ".env",
    ".eslintrc",
    ".npmrc",
    "babel.config.js",
    "eslint.config.js",
    "package.json",
    "pyproject.toml",
    "rollup.config.js",
    "tsconfig.json",
    "vite.config.ts",
    "webpack.config.js",
}

GENERATED_PARTS = {"generated", "__generated__", "gen"}


def risk_hints(path: str) -> list[str]:
    normalized = path.replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    name = pure_path.name
    lower_name = name.lower()
    parts = {part.lower() for part in pure_path.parts}

    hints: list[str] = []
    if name in LOCKFILES or lower_name.endswith(".lock"):
        hints.append("lockfile")
    if _is_config_path(normalized, name, lower_name):
        hints.append("config")
    if _is_generated_path(parts, lower_name):
        hints.append("generated")
    return hints


def _is_config_path(path: str, name: str, lower_name: str) -> bool:
    if name in CONFIG_NAMES:
        return True
    if lower_name.endswith((".config.js", ".config.ts", ".config.mjs", ".config.cjs")):
        return True
    if path.startswith(".github/workflows/"):
        return True
    return lower_name.startswith(".env.")


def _is_generated_path(parts: set[str], lower_name: str) -> bool:
    if parts & GENERATED_PARTS:
        return True
    return any(
        marker in lower_name
        for marker in (".generated.", ".gen.", ".pb.", "_pb.")
    )
