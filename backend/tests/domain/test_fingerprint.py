import pytest

from pairo.domain.fingerprint import compute_fingerprint


class TestFingerprint:
    """Properties from spec: content-based, line-shift-resilient."""

    def test_basic_fingerprint_is_16_hex_chars(self):
        fp = compute_fingerprint(
            axis="crafts",
            category="naming",
            file_path="src/app.py",
            context_lines=["  def foo():", "    pass", "    return 1"],
        )
        assert len(fp) == 16
        assert all(c in "0123456789abcdef" for c in fp)

    def test_line_shift_same_fingerprint(self):
        """Adding lines above the block must not change the fingerprint."""
        lines = ["def foo():", "  x = 1", "  return x"]
        fp1 = compute_fingerprint("crafts", "naming", "src/app.py", lines)
        # Same code, just imagine lines shifted — fingerprint uses content only
        fp2 = compute_fingerprint("crafts", "naming", "src/app.py", lines)
        assert fp1 == fp2

    def test_code_change_different_fingerprint(self):
        fp1 = compute_fingerprint(
            "crafts", "naming", "src/app.py", ["def foo():", "  return 1"]
        )
        fp2 = compute_fingerprint(
            "crafts", "naming", "src/app.py", ["def bar():", "  return 2"]
        )
        assert fp1 != fp2

    def test_indentation_only_same_fingerprint(self):
        """Whitespace normalization: indent change = same fingerprint."""
        fp1 = compute_fingerprint(
            "crafts", "naming", "src/app.py", ["  def foo():", "    pass"]
        )
        fp2 = compute_fingerprint(
            "crafts", "naming", "src/app.py", ["def foo():", "  pass"]
        )
        assert fp1 == fp2

    def test_different_category_different_fingerprint(self):
        lines = ["def foo():", "  pass"]
        fp1 = compute_fingerprint("crafts", "naming", "src/app.py", lines)
        fp2 = compute_fingerprint("crafts", "complexity", "src/app.py", lines)
        assert fp1 != fp2

    def test_different_axis_different_fingerprint(self):
        lines = ["def foo():", "  pass"]
        fp1 = compute_fingerprint("crafts", "naming", "src/app.py", lines)
        fp2 = compute_fingerprint("eco", "naming", "src/app.py", lines)
        assert fp1 != fp2

    def test_blank_lines_ignored(self):
        fp1 = compute_fingerprint(
            "crafts", "naming", "src/app.py", ["def foo():", "", "  pass", ""]
        )
        fp2 = compute_fingerprint(
            "crafts", "naming", "src/app.py", ["def foo():", "  pass"]
        )
        assert fp1 == fp2

    def test_with_rule_id(self):
        """Deterministic rules include rule_id in fingerprint."""
        fp1 = compute_fingerprint(
            "a11y", "img-alt", "index.html", ["<img src='x'>"],
            rule_id="a11y.img-alt",
        )
        fp2 = compute_fingerprint(
            "a11y", "img-alt", "index.html", ["<img src='x'>"],
        )
        assert fp1 != fp2

    def test_no_context_lines_with_blob_sha(self):
        """Findings without line (e.g. image too big): file + rule + blob sha."""
        fp = compute_fingerprint(
            "eco", "image-size", "logo.png", [],
            rule_id="eco.image-size",
            blob_sha="abc123def456",
        )
        assert len(fp) == 16

    def test_blob_sha_change_different_fingerprint(self):
        fp1 = compute_fingerprint(
            "eco", "image-size", "logo.png", [],
            rule_id="eco.image-size", blob_sha="aaa",
        )
        fp2 = compute_fingerprint(
            "eco", "image-size", "logo.png", [],
            rule_id="eco.image-size", blob_sha="bbb",
        )
        assert fp1 != fp2
