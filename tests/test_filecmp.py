# pylint: disable=missing-function-docstring
# pylint: disable=use-implicit-booleaness-not-comparison
"""Test filecmp."""
import filecmp
import tempfile
from os import path
from webdriver_browser.patch import pack_dir_with_ref, unpack_dir_with_ref, generate_dir_hash, generate_dir_diff_with_ref


current_dir = path.dirname(__file__)


def test_filecmp():
    assert filecmp.cmp(path.join(current_dir, "default", "same.txt"),
                       path.join(current_dir, "other", "same.txt"), shallow=False)
    assert not filecmp.cmp(path.join(current_dir, "default", "diff.txt"),
                           path.join(current_dir, "other", "diff.txt"), shallow=False)


def test_generate_dir_diff_with_ref():
    diff = generate_dir_diff_with_ref(path.join(current_dir, 'default'), path.join(current_dir, 'other'))
    assert set(diff["left_only"].keys()) == {path.join('.', 'left.txt'),
                                             path.join('.', 'left'), path.join('.', 'folder', 'empty')}
    assert set(diff["right_only"].keys()) == {path.join('.', 'right.txt'), path.join(
        '.', 'right'), path.join('.', 'right', 'right.txt'), path.join('.', 'folder', 'null')}
    assert set(diff["common"].keys()) == {path.join('.', 'folder'), path.join(
        '.', 'same.txt'), path.join('.', 'same'), path.join('.', 'same', 'same.txt')}
    assert set(diff["diff_files"].keys()) == {path.join('.', 'diff.txt')}


def test_dircmp():
    diffs = filecmp.dircmp(path.join(current_dir, "default"), path.join(current_dir, "other"))
    assert set(diffs.left_only) == {'left', 'left.txt'}
    assert set(diffs.right_only) == {'right', 'right.txt'}
    assert set(diffs.diff_files) == {'diff.txt'}
    assert set(diffs.same_files) == {'same.txt'}
    assert set(diffs.common_dirs) == {'same', 'folder'}


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
    assert set(diffs.common_files) == {'diff.txt', 'same.txt', 'right.txt'}
    assert generate_dir_hash(path.join(current_dir, "other")) == generate_dir_hash(tmp_dir)
