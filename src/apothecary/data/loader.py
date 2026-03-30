"""Load substance profiles from YAML files into validated Pydantic models."""

from pathlib import Path

import yaml

from apothecary.models.substance import Substance


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
        """Search substances by name, ID, or common names (case-insensitive)."""
        query_lower = query.lower()
        results = []
        for substance in self._substances.values():
            if query_lower in substance.id.lower():
                results.append(substance)
            elif query_lower in substance.name.lower():
                results.append(substance)
            elif any(query_lower in cn.lower() for cn in substance.common_names):
                results.append(substance)
        return results

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
