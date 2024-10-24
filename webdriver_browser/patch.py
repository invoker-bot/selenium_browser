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
    for root, dirs, files in walk(directory):
        relroot = path.relpath(root, directory)
        for file in files:
            fullpath = path.join(root, file)
            if path.isfile(fullpath):
                with open(fullpath, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()
                relpath = path.join(relroot, file)
                hash_dict[relpath] = sha
        for dir_ in dirs:
            relpath = path.join(relroot, dir_)
            hash_dict[relpath] = None
    return hash_dict


def generate_dir_diff_with_ref(ref_dir: str, src_dir: str, relpath="."):  # pylint: disable=too-many-locals
    """Generate a diff of a directory with a reference directory."""
    diff_with_ref = {
        "left_only": {

        },
        "common": {

        },
        "right_only": {

        },
        "diff_files": {

        },
    }
    ref_dir_start = path.join(ref_dir, relpath)
    src_dir_start = path.join(src_dir, relpath)
    comparsion = filecmp.dircmp(ref_dir_start, src_dir_start)
    for file in comparsion.left_only:
        diff_with_ref["left_only"][path.join(relpath, file)] = None if path.isdir(path.join(ref_dir_start, file)) else True
    for file in comparsion.same_files:
        diff_with_ref["common"][path.join(relpath, file)] = None if path.isdir(path.join(ref_dir_start, file)) else True
    for file in comparsion.right_only:
        right_path = path.join(src_dir_start, file)
        if path.isdir(right_path):
            diff_with_ref["right_only"][path.join(relpath, file)] = None
            for root, dirs, files in walk(right_path):
                for file in files:
                    fullpath = path.join(root, file)
                    with open(fullpath, "rb") as f:
                        diff_with_ref["right_only"][path.join(relpath, path.relpath(fullpath, src_dir_start))] = f.read()
                for dir_ in dirs:
                    fullpath = path.join(root, dir_)
                    diff_with_ref["right_only"][path.join(relpath, path.relpath(fullpath, src_dir_start))] = None
        elif path.isfile(right_path):
            with open(right_path, "rb") as f:
                diff_with_ref["right_only"][path.join(relpath, file)] = f.read()
    for file in comparsion.diff_files:
        with open(path.join(ref_dir_start, file), "rb") as f:
            ref_file = blockchecksums(f)
        with open(path.join(src_dir_start, file), "rb") as f:
            delta = rsyncdelta(f, ref_file)
        diff_with_ref["diff_files"][path.join(relpath, file)] = delta
    for folder in comparsion.common_dirs:
        diff_with_ref["common"][path.join(relpath, folder)] = None
        sub_diff_with_ref = generate_dir_diff_with_ref(ref_dir, src_dir, path.join(relpath, folder))
        for key, value in diff_with_ref.items():
            value.update(sub_diff_with_ref[key])
    return diff_with_ref


def pack_dir_with_ref(ref_dir: str, zip_path: str, src_dir: str, remove=True):
    """Pack a directory with a reference directory."""
    diff_with_ref = generate_dir_diff_with_ref(ref_dir, src_dir)
    diff_with_ref["hash"] = generate_dir_hash(ref_dir)
    with open(zip_path, "wb") as f:
        f.write(zlib.compress(pickle.dumps(diff_with_ref)))
    if remove:
        shutil.rmtree(src_dir)


def unpack_dir_with_ref(ref_dir: str, zip_path: str, dist_dir: str, remove=True):  # pylint: disable=too-many-locals
    """Unpack a directory with a reference directory."""
    with open(zip_path, "rb") as f:
        diff_with_ref = pickle.loads(zlib.decompress(f.read()))
    hash_dict = diff_with_ref.get("hash", None)
    if hash_dict is not None:
        if generate_dir_hash(ref_dir) != hash_dict:
            raise ValueError(f"reference directory '{ref_dir}' changed")
    makedirs(dist_dir, exist_ok=True)
    for file, is_file in diff_with_ref["common"].items():
        if is_file is not None:
            makedirs(path.dirname(path.join(dist_dir, file)), exist_ok=True)
            shutil.copy(path.join(ref_dir, file), path.join(dist_dir, file), follow_symlinks=False)
        else:
            makedirs(path.join(dist_dir, file), exist_ok=True)
    for file, data in diff_with_ref["right_only"].items():
        if data is not None:
            makedirs(path.dirname(path.join(dist_dir, file)), exist_ok=True)
            with open(path.join(dist_dir, file), "wb") as f:
                f.write(data)
        else:
            makedirs(path.join(dist_dir, file), exist_ok=True)
    for file, delta in diff_with_ref["diff_files"].items():
        with open(path.join(ref_dir, file), "rb") as ref_file:
            makedirs(path.dirname(path.join(dist_dir, file)), exist_ok=True)
            with open(path.join(dist_dir, file), "wb") as f:
                patchstream(ref_file, f, delta)

    for file in diff_with_ref["left_only"].keys():
        p = path.join(dist_dir, file)
        if path.exists(p):
            if path.isdir(p):
                shutil.rmtree(p)
            else:
                remove_file(p)

    if remove:
        remove_file(zip_path)
