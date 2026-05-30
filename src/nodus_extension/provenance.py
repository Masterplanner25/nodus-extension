from __future__ import annotations

from enum import Enum


class Origin(str, Enum):
    local = "local"
    registry = "registry"
    git = "git"


class TrustClass(str, Enum):
    dev = "dev"
    verified = "verified"
    trusted = "trusted"


class OwnerClass(str, Enum):
    personal = "personal"
    team = "team"
    org = "org"


class Provenance:
    __slots__ = ("origin", "trust_class", "owner_class")

    def __init__(
        self,
        origin: Origin = Origin.local,
        trust_class: TrustClass = TrustClass.dev,
        owner_class: OwnerClass = OwnerClass.personal,
    ) -> None:
        self.origin = Origin(origin)
        self.trust_class = TrustClass(trust_class)
        self.owner_class = OwnerClass(owner_class)

    def as_dict(self) -> dict:
        return {
            "origin": self.origin.value,
            "trust_class": self.trust_class.value,
            "owner_class": self.owner_class.value,
        }

    def __repr__(self) -> str:
        return (
            f"Provenance(origin={self.origin!r}, trust_class={self.trust_class!r}, "
            f"owner_class={self.owner_class!r})"
        )
