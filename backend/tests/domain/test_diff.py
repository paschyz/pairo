from pairo.domain.diff import AddedLine, parse_patch

SIMPLE_PATCH = """\
@@ -1,4 +1,6 @@
 line one
+added line two
+added line three
 line four
 line five
 line six"""


def test_parse_simple_patch() -> None:
    lines = parse_patch(SIMPLE_PATCH)
    assert lines == [
        AddedLine(number=2, content="added line two"),
        AddedLine(number=3, content="added line three"),
    ]


MULTI_HUNK_PATCH = """\
@@ -1,3 +1,4 @@
 first
+inserted at 2
 third
 fourth
@@ -10,3 +11,4 @@
 ten
 eleven
+inserted at 13
 thirteen"""


def test_parse_multi_hunk_patch() -> None:
    lines = parse_patch(MULTI_HUNK_PATCH)
    assert lines == [
        AddedLine(number=2, content="inserted at 2"),
        AddedLine(number=13, content="inserted at 13"),
    ]


def test_parse_empty_patch() -> None:
    assert parse_patch("") == []


def test_parse_deletion_only_patch() -> None:
    patch = """\
@@ -1,3 +1,2 @@
 keep
-removed
 keep"""
    lines = parse_patch(patch)
    assert lines == []


NO_NEWLINE_PATCH = """\
@@ -1,2 +1,3 @@
 existing
+new line
+another
\\ No newline at end of file"""


def test_parse_patch_with_no_newline_marker() -> None:
    lines = parse_patch(NO_NEWLINE_PATCH)
    assert lines == [
        AddedLine(number=2, content="new line"),
        AddedLine(number=3, content="another"),
    ]


REAL_GITHUB_PATCH = """\
@@ -0,0 +1,5 @@
+<template>
+  <img src="logo.png">
+  <img src="icon.svg" alt="icon">
+</template>
+<script setup lang="ts"></script>"""


def test_parse_new_file_patch() -> None:
    lines = parse_patch(REAL_GITHUB_PATCH)
    assert len(lines) == 5
    assert lines[0] == AddedLine(number=1, content="<template>")
    assert lines[4] == AddedLine(number=5, content='<script setup lang="ts"></script>')
