# pylint: disable=missing-function-docstring
# pylint: disable=use-implicit-booleaness-not-comparison
"""Test filecmp."""
import filecmp
import tempfile
from os import path
from selenium_browser.zip import pack_dir_with_ref, unpack_dir_with_ref


current_dir = path.dirname(__file__)


def test_filecmp():
    assert filecmp.cmp(path.join(current_dir, "default", "same.txt"), path.join(current_dir, "other", "same.txt"))
    assert not filecmp.cmp(path.join(current_dir, "default", "diff.txt"), path.join(current_dir, "other", "diff.txt"))


def test_dircmp():
    diffs = filecmp.dircmp(path.join(current_dir, "default"), path.join(current_dir, "other"))
    assert set(diffs.left_only) == {'left.txt'}
    assert set(diffs.right_only) == {'right.txt'}
    assert set(diffs.diff_files) == {'diff.txt'}
    assert set(diffs.same_files) == {'same.txt'}
    assert set(diffs.common) == {'diff.txt', 'same.txt'}


def test_zip():
    tmp_zip = tempfile.mktemp()
    tmp_dir = tempfile.mkdtemp()
    pack_dir_with_ref(path.join(current_dir, "default"), tmp_zip, path.join(current_dir, "other"), remove=False)
    unpack_dir_with_ref(path.join(current_dir, "default"), tmp_zip, tmp_dir, remove=True)
    diffs = filecmp.dircmp(path.join(current_dir, "other"), tmp_dir)
    assert len(diffs.left_only) == 0
    assert len(diffs.right_only) == 0
    assert len(diffs.diff_files) == 0
    assert set(diffs.same_files) == {'diff.txt', 'same.txt', 'right.txt'}
    assert set(diffs.common) == {'diff.txt', 'same.txt', 'right.txt'}
