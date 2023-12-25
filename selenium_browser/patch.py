"""Pack and unpack a directory with a reference directory."""
import zlib
import pickle
import shutil
import filecmp
from os import path, makedirs, remove as remove_file
from .rsync import blockchecksums, rsyncdelta, patchstream


def pack_dir_with_ref(ref_dir: str, zip_path: str, src_dir: str, remove=True):
    """Pack a directory with a reference directory."""
    diff_with_ref = {
        "left_only": {

        },
        "same_files": {

        },
        "right_only": {

        },
        "diff_files": {

        },
    }
    comparsion = filecmp.dircmp(ref_dir, src_dir)
    for file in comparsion.left_only:
        diff_with_ref["left_only"][file] = path.isdir(path.join(ref_dir, file))
    for file in comparsion.same_files:
        diff_with_ref["same_files"][file] = path.isdir(path.join(ref_dir, file))
    for file in comparsion.right_only:
        with open(path.join(src_dir, file), "rb") as f:
            diff_with_ref["right_only"][file] = f.read()
    for file in comparsion.diff_files:
        with open(path.join(ref_dir, file), "rb") as f:
            ref_file = blockchecksums(f)
        with open(path.join(src_dir, file), "rb") as f:
            delta = rsyncdelta(f, ref_file)
            diff_with_ref["diff_files"][file] = delta
    with open(zip_path, "wb") as f:
        f.write(zlib.compress(pickle.dumps(diff_with_ref)))
    if remove:
        shutil.rmtree(src_dir)


def unpack_dir_with_ref(ref_dir: str, zip_path: str, dst_dir: str, remove=True):
    """Unpack a directory with a reference directory."""
    with open(zip_path, "rb") as f:
        diff_with_ref = pickle.loads(zlib.decompress(f.read()))
    makedirs(dst_dir, exist_ok=True)
    for file, is_dir in diff_with_ref["same_files"].items():
        if is_dir:
            makedirs(path.join(dst_dir, file), exist_ok=True)
        else:
            shutil.copy(path.join(ref_dir, file), path.join(dst_dir, file), follow_symlinks=False)

    for file, data in diff_with_ref["right_only"].items():
        with open(path.join(dst_dir, file), "wb") as f:
            f.write(data)
    for file, delta in diff_with_ref["diff_files"].items():
        with open(path.join(ref_dir, file), "rb") as ref_file:
            with open(path.join(dst_dir, file), "wb") as f:
                patchstream(ref_file, f, delta)

    for file, is_dir in diff_with_ref["left_only"].items():
        p = path.join(dst_dir, file)
        if path.exists(p):
            if path.isdir(p):
                shutil.rmtree(p)
            else:
                remove_file(p)

    if remove:
        remove_file(zip_path)
