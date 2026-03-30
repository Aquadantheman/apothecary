"""User stack model — everything a person takes."""

from pydantic import BaseModel


class StackEntry(BaseModel):
    """A single substance in a user's stack with their specific usage details."""

    substance_id: str  # Reference to substance database
    dose_mg: float | None = None
    frequency: str = "daily"  # "daily", "as_needed", "twice_daily", etc.
    formulation: str | None = None  # "IR", "XR", specific brand
    current_timing: str | None = None  # When they currently take it
    notes: str | None = None


class UserStack(BaseModel):
    """A user's complete substance stack.

    This is the input to the analysis engines. It references
    substances by ID, which are resolved against the database.
    """

    entries: list[StackEntry]
    wake_time: str = "07:00"
    sleep_target: str = "23:00"
    notes: str | None = None

    @property
    def substance_ids(self) -> list[str]:
        return [e.substance_id for e in self.entries]

    def get_entry(self, substance_id: str) -> StackEntry | None:
        for entry in self.entries:
            if entry.substance_id == substance_id:
                return entry
        return None
