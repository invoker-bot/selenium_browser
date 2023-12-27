"""Pack and unpack a directory with a reference directory."""
import zlib
import pickle
import hashlib
import shutil
import filecmp
from os import path, makedirs, remove as remove_file, walk
from .rsync import blockchecksums, rsyncdelta, patchstream


def generate_dir_hash(directory: str):
    """Generate a hash of a directory."""
    hash_dict = {}
    for root, _dirs, files in walk(directory):
        relroot = path.relpath(root, directory)
        for file in files:
            fullpath = path.join(root, file)
            size = path.getsize(fullpath)
            with open(fullpath, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            relpath = path.join(relroot, file)
            hash_dict[relpath] = [sha, size]
    return hash_dict


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
    diff_with_ref["hash"] = generate_dir_hash(ref_dir)
    with open(zip_path, "wb") as f:
        f.write(zlib.compress(pickle.dumps(diff_with_ref)))
    if remove:
        shutil.rmtree(src_dir)


def unpack_dir_with_ref(ref_dir: str, zip_path: str, dst_dir: str, remove=True):
    """Unpack a directory with a reference directory."""
    with open(zip_path, "rb") as f:
        diff_with_ref = pickle.loads(zlib.decompress(f.read()))
    hash_dict = diff_with_ref.get("hash", None)
    if hash_dict is not None:
        if generate_dir_hash(ref_dir) != hash_dict:
            print(generate_dir_hash(ref_dir))
            raise ValueError(f"reference directory '{ref_dir}' changed")
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
