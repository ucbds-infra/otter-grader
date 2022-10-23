"""Utilities for Otter Generate"""

import os


def zip_folder(zf, path, prefix="", exclude=[]):
    """
    Recursively add the contents of a directory into a ``zipfile.ZipFile``.

    Args:
        zf (``zipfile.ZipFile``): the open zip file object to add to
        path (``str``): an absolute path to the directory to add to the zip file
        prefix (``str``, optional): a prefix to add to the basename of the path for the archive name
    """
    if not os.path.isabs(path):
        raise ValueError("'path' must be absolute path")

    parent_basename = os.path.basename(path)
    for file in os.listdir(path):
        if file in exclude:
            continue
        child_path = os.path.join(path, file)

        if os.path.isfile(child_path):
            arcname = os.path.join(prefix, parent_basename, file)
            zf.write(child_path, arcname=arcname)

        elif os.path.isdir(child_path):
            zip_folder(zf, child_path, prefix=os.path.join(prefix, parent_basename))


def _get_dep_name(d):
    """
    Determine the name of a dependency, ignoring version information.

    Args:
        d (``str``): the dependency

    Returns:
        ``str``: the dependency name
    """
    if "+" in d:
        return d
    return d.split(">")[0].split("<")[0].split("=")[0]


def merge_conda_environments(e1, e2, name):
    """
    Merge two conda environments into a single environment with the specified name.

    Merges the channels, dependencies, and pip dependencies of two conda environments. If ``e1`` and
    ``e2`` conflict, the values in ``e1`` are taken.

    Args:
        e1 (``dict[str, object]``): the first conda environment
        e2 (``dict[str, object]``): the second conda environment
        name (``str``): the resulting environment name

    Returns:
        ``dict[str, object]``: the merged conda environment
    """
    e = {"name": name, "channels": e1.get("channels", []), "dependencies": []}
    e["channels"].extend([c for c in e2.get("channels", []) if c not in e["channels"]])

    if not e["channels"]:
        e.pop("channels")

    seen_deps, dicts = set(), []

    def handle_dep(d, target):
        if isinstance(d, dict):
            dicts.append(d)
            return
        if not isinstance(d, str):
            raise TypeError(f"Value of invalid type in dependencies list: {d}")
        dep_name = _get_dep_name(d)
        if dep_name not in seen_deps:
            seen_deps.add(dep_name)
            target.append(d)

    for ei in [e1, e2]:
        for d in ei["dependencies"]:
            handle_dep(d, e["dependencies"])

    if len(dicts) > 2:
        raise ValueError("Too many dictionaries found in environment dependencies")

    if len(dicts) == 1:
        e["dependencies"].append(dicts[0])

    elif len(dicts) == 2:
        target = []
        e["dependencies"].append({"pip": target})
        for di in dicts:
            if set(di.keys()) != {"pip"}:
                raise ValueError("Dictionaries should only contain the pip key")
            for d in di["pip"]:
                handle_dep(d, target)

    return e
