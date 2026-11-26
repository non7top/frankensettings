"""The 'missing' report: which keys each side lacks."""
from .merge import strip_prefix


def _key_paths(data, strip):
    paths = set()
    for raw, value in data.items():
        here = (strip_prefix(raw)[0] if strip else raw,)
        paths.add(here)
        if isinstance(value, dict):
            paths.update(here + sub for sub in _key_paths(value, strip))
    return paths


def _dotted(paths):
    return sorted(".".join(path) for path in paths)


def _group(title, empty_title, marker, keys):
    if not keys:
        return [empty_title]
    return [title] + [f"  {marker} {key}" for key in keys]


def missing_report(template, target, excludes, template_path, target_path):
    excludes = frozenset(excludes)
    template_paths = _key_paths(template, True)
    target_paths = _key_paths(target, False)

    def private(path):
        return any(segment in excludes for segment in path)

    lacking = _dotted(p for p in template_paths - target_paths if not private(p))
    unmanaged = _dotted(p for p in target_paths - template_paths if not private(p))
    excluded = _dotted(p for p in target_paths if private(p))

    blocks = [
        [f"Template: {template_path}", f"Target:   {target_path}"],
        _group(
            "Missing from target (generic template settings not yet in target):",
            "Missing from target: (none)",
            "+",
            lacking,
        ),
        _group(
            "Missing from template (unmanaged settings in target):",
            "Missing from template: (none)",
            "?",
            unmanaged,
        ),
    ]
    if excluded:
        header = f"Excluded private settings present in target ({len(excluded)}):"
        blocks.append([header] + [f"  * {key}" for key in excluded])
    return "\n\n".join("\n".join(block) for block in blocks) + "\n"
