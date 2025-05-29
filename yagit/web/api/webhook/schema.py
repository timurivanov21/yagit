from dataclasses import dataclass


@dataclass
class RuleDTO:
    id: int
    tracker_token: str
    tracker_org_id: str
    tracker_column_id: str
