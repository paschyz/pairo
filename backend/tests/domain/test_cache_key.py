"""Tests for deterministic cache key computation."""

from pairo.domain.cache_key import compute_cache_key


class TestCacheKey:
    def test_basic_key_is_64_hex(self):
        key = compute_cache_key(
            files_content={"app.py": "+ def foo():\n+   pass"},
            axes=["crafts", "eco"],
            config_hash="cfg1",
            prompt_version="1",
            model="gemini-3.6-flash",
        )
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_same_input_same_key(self):
        args = dict(
            files_content={"a.py": "+ x = 1"},
            axes=["crafts"],
            config_hash="c",
            prompt_version="1",
            model="gemini",
        )
        assert compute_cache_key(**args) == compute_cache_key(**args)

    def test_different_content_different_key(self):
        base = dict(axes=["crafts"], config_hash="c", prompt_version="1", model="m")
        k1 = compute_cache_key(files_content={"a.py": "+ x = 1"}, **base)
        k2 = compute_cache_key(files_content={"a.py": "+ x = 2"}, **base)
        assert k1 != k2

    def test_different_prompt_version_different_key(self):
        base = dict(
            files_content={"a.py": "+ x"},
            axes=["crafts"],
            config_hash="c",
            model="m",
        )
        k1 = compute_cache_key(prompt_version="1", **base)
        k2 = compute_cache_key(prompt_version="2", **base)
        assert k1 != k2

    def test_different_model_different_key(self):
        base = dict(
            files_content={"a.py": "+ x"},
            axes=["crafts"],
            config_hash="c",
            prompt_version="1",
        )
        k1 = compute_cache_key(model="gemini-3.6-flash", **base)
        k2 = compute_cache_key(model="gemini-4.0-pro", **base)
        assert k1 != k2

    def test_different_axes_different_key(self):
        base = dict(
            files_content={"a.py": "+ x"},
            config_hash="c",
            prompt_version="1",
            model="m",
        )
        k1 = compute_cache_key(axes=["crafts"], **base)
        k2 = compute_cache_key(axes=["crafts", "eco"], **base)
        assert k1 != k2

    def test_file_order_irrelevant(self):
        base = dict(
            axes=["crafts"],
            config_hash="c",
            prompt_version="1",
            model="m",
        )
        k1 = compute_cache_key(
            files_content={"a.py": "+ x", "b.py": "+ y"}, **base
        )
        k2 = compute_cache_key(
            files_content={"b.py": "+ y", "a.py": "+ x"}, **base
        )
        assert k1 == k2
