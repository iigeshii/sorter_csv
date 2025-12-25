import json
import sys
from pathlib import Path


CATEGORIES_JSON = Path("categories.json")
LAYOUT_JSON = Path("category_layout.json")


def load_json(path: Path) -> object:
    if not path.exists():
        raise FileNotFoundError(f"Could not find: {path.resolve()}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_categories(path: Path) -> dict[str, list[str]]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise TypeError(f"{path.name} must be a JSON object (dict) at top level.")
    # basic shape check
    for k, v in data.items():
        if not isinstance(k, str):
            raise TypeError(f"{path.name}: category keys must be strings. Bad key: {k!r}")
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise TypeError(
                f"{path.name}: each category value must be a list[str]. "
                f"Bad value for {k!r}: {type(v)}"
            )
    return data


def load_layout(path: Path) -> dict[str, list[str]]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise TypeError(f"{path.name} must be a JSON object (dict) at top level.")
    # basic shape check
    for k, v in data.items():
        if not isinstance(k, str):
            raise TypeError(f"{path.name}: category keys must be strings. Bad key: {k!r}")
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise TypeError(
                f"{path.name}: each category value must be a list[str] of cluster IDs. "
                f"Bad value for {k!r}: {type(v)}"
            )
    return data


def validate_same_categories(
    categories: dict[str, list[str]],
    layout: dict[str, list[str]],
) -> None:
    cat_set = set(categories.keys())
    layout_set = set(layout.keys())

    only_in_categories = sorted(cat_set - layout_set, key=str.casefold)
    only_in_layout = sorted(layout_set - cat_set, key=str.casefold)

    if only_in_categories or only_in_layout:
        print("\n[ERROR] Category mismatch between JSON files.\n")

        if only_in_categories:
            print(f"Categories present in {CATEGORIES_JSON.name} but missing in {LAYOUT_JSON.name}:")
            for c in only_in_categories:
                print(f"  - {c}")
            print()

        if only_in_layout:
            print(f"Categories present in {LAYOUT_JSON.name} but missing in {CATEGORIES_JSON.name}:")
            for c in only_in_layout:
                print(f"  - {c}")
            print()

        print("Fix the mismatch and run again.")
        sys.exit(2)

def validate_layout_bins_unique(layout: dict[str, list[str]]) -> None:
    """
    Validate:
      1) No bin/cluster (e.g. 'A1') is assigned to more than one category.
      2) No category lists the same bin more than once.
    """
    # (2) duplicates within a category
    category_dupes: dict[str, list[str]] = {}
    for category, bins in layout.items():
        seen = set()
        dupes = []
        for b in bins:
            if b in seen and b not in dupes:
                dupes.append(b)
            seen.add(b)
        if dupes:
            category_dupes[category] = dupes

    # (1) overlaps across categories
    bin_to_categories: dict[str, list[str]] = {}
    for category, bins in layout.items():
        for b in bins:
            bin_to_categories.setdefault(b, []).append(category)

    overlaps = {b: cats for b, cats in bin_to_categories.items() if len(cats) > 1}

    if category_dupes or overlaps:
        print("\n[ERROR] Invalid bin assignments in category_layout.json.\n")

        if category_dupes:
            print("Duplicate bins listed within the same category:")
            for category in sorted(category_dupes.keys(), key=str.casefold):
                dupes = ", ".join(sorted(category_dupes[category], key=str.casefold))
                print(f"  - {category}: {dupes}")
            print()

        if overlaps:
            print("Bins assigned to multiple categories:")
            for b in sorted(overlaps.keys(), key=str.casefold):
                cats = ", ".join(sorted(overlaps[b], key=str.casefold))
                print(f"  - {b}: {cats}")
            print()

        print("Fix the issues and run again.")
        sys.exit(3)

def print_sorted_categories(categories: dict[str, list[str]]) -> None:
    for category in sorted(categories.keys(), key=str.casefold):
        items = sorted(categories[category], key=str.casefold)
        print(f"\n=== {category} ({len(items)} items) ===")
        for idx, item in enumerate(items, start=1):
            print(f"  {idx:2d}. {item}")


def main() -> None:
    categories = load_categories(CATEGORIES_JSON)
    layout = load_layout(LAYOUT_JSON)

    validate_same_categories(categories, layout)
    validate_layout_bins_unique(layout)


    # If we got here, they match.
    print_sorted_categories(categories)


if __name__ == "__main__":
    main()
