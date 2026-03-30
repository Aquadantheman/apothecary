"""Load substance profiles from YAML files into validated Pydantic models."""

from pathlib import Path

import yaml

from apothecary.models.substance import Substance


def _fuzzy_match(query: str, target: str, max_distance: int = 2) -> bool:
    """Check if query is within edit distance of target.

    Simple Levenshtein distance — returns True if the query
    is close enough to the target to be a likely typo.
    """
    if abs(len(query) - len(target)) > max_distance:
        return False

    # For short words, require closer match
    if len(query) <= 4:
        max_distance = 1

    # Simple Levenshtein
    m, n = len(query), len(target)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if query[i - 1] == target[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp

    return dp[n] <= max_distance


class SubstanceDatabase:
    """In-memory substance database loaded from curated YAML files.

    Usage:
        db = SubstanceDatabase()
        db.load_directory(Path("src/apothecary/data/curated"))
        adderall = db.get("adderall")
    """

    def __init__(self) -> None:
        self._substances: dict[str, Substance] = {}

    def load_file(self, path: Path) -> Substance:
        """Load a single substance YAML file."""
        with open(path) as f:
            raw = yaml.safe_load(f)

        data = raw.get("substance", raw)
        substance = Substance.model_validate(data)
        self._substances[substance.id] = substance
        return substance

    def load_directory(self, directory: Path) -> int:
        """Recursively load all .yaml/.yml files from a directory.

        Returns the number of substances loaded.
        """
        count = 0
        for path in sorted(directory.rglob("*.yaml")):
            try:
                self.load_file(path)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load {path}: {e}")
        for path in sorted(directory.rglob("*.yml")):
            try:
                self.load_file(path)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load {path}: {e}")
        return count

    def get(self, substance_id: str) -> Substance | None:
        """Look up a substance by ID."""
        return self._substances.get(substance_id)

    def search(self, query: str) -> list[Substance]:
        """Search substances by name, ID, common names, or category.

        Uses substring matching first, then falls back to fuzzy matching
        for typos (edit distance <= 2).
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return []

        exact_results = []
        fuzzy_results = []

        for substance in self._substances.values():
            # Exact substring matches (high confidence)
            searchable = [
                substance.id.lower(),
                substance.name.lower(),
                substance.category.lower().replace("_", " "),
            ] + [cn.lower() for cn in substance.common_names]

            if any(query_lower in field for field in searchable):
                exact_results.append(substance)
                continue

            # Fuzzy matching for typos (lower confidence)
            if len(query_lower) >= 3:
                for field in searchable:
                    # Check each word in the field
                    for word in field.split():
                        if _fuzzy_match(query_lower, word):
                            fuzzy_results.append(substance)
                            break
                    else:
                        continue
                    break

        # Return exact matches first, then fuzzy
        return exact_results + fuzzy_results

    def all(self) -> list[Substance]:
        """Return all loaded substances."""
        return list(self._substances.values())

    @property
    def count(self) -> int:
        return len(self._substances)

    def __contains__(self, substance_id: str) -> bool:
        return substance_id in self._substances

    def __repr__(self) -> str:
        return f"SubstanceDatabase({self.count} substances)"
