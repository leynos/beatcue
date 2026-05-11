"""Architecture policies for BeatCue hexagonal boundary enforcement."""

from __future__ import annotations

import dataclasses as dc


@dc.dataclass(frozen=True, slots=True)
class ModuleGroup:
    """One named architecture group and the groups it may import.

    Parameters
    ----------
    name
        Stable group name used in diagnostics and dependency rules.
    module_prefixes
        Dotted module prefixes that belong to this group.
    allowed_groups
        Group names this group may import without producing a violation.

    """

    name: str
    module_prefixes: tuple[str, ...]
    allowed_groups: frozenset[str]

    def contains(self, module_name: str) -> bool:
        """Return whether a module belongs to this architecture group.

        Parameters
        ----------
        module_name
            Dotted module name being classified.

        Returns
        -------
        bool
            True when ``module_name`` is equal to or below one of this group's
            module prefixes.

        """
        return any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in self.module_prefixes
        )


@dc.dataclass(frozen=True, slots=True)
class ArchitecturePolicy:
    """Dependency-direction policy for a package tree.

    Parameters
    ----------
    groups
        Ordered architecture groups. The first matching group classifies a
        module.
    rule_id
        Stable diagnostic identifier emitted for violations.

    """

    groups: tuple[ModuleGroup, ...]
    rule_id: str = "ARCH001"

    def group_for(self, module_name: str) -> ModuleGroup | None:
        """Return the first matching architecture group, if any.

        Parameters
        ----------
        module_name
            Dotted module name to classify.

        Returns
        -------
        ModuleGroup | None
            The first group whose prefixes contain ``module_name``, or None
            when the policy does not classify the module.

        """
        for group in self.groups:
            if group.contains(module_name):
                return group
        return None


_INFRASTRUCTURE_MODULES: tuple[str, ...] = (
    "cmdmox",
    "cuprum",
    "cv2",
    "cyclopts",
    "librosa",
    "rich",
    "transformers",
)


def _beatcue_groups(package: str) -> tuple[ModuleGroup, ...]:
    """Return BeatCue production groups for one package name.

    BeatCue's policy models the documented hexagonal dependency direction:
    ``composition_root`` may import every group, ``domain`` is isolated,
    ``application`` may import domain contracts, and adapters may bridge to
    infrastructure.

    Parameters
    ----------
    package
        Root package name whose modules should be classified.

    Returns
    -------
    tuple[ModuleGroup, ...]
        Ordered architecture groups and dependency rules for ``package``.

    """
    all_groups = frozenset({
        "adapter",
        "application",
        "composition_root",
        "domain",
        "inbound_adapter",
        "infrastructure",
        "outbound_adapter",
    })
    adapter_allowed = frozenset({
        "adapter",
        "application",
        "domain",
        "infrastructure",
        "inbound_adapter",
        "outbound_adapter",
    })
    return (
        ModuleGroup(
            name="composition_root",
            module_prefixes=(f"{package}.config",),
            allowed_groups=all_groups,
        ),
        ModuleGroup(
            name="domain",
            module_prefixes=(f"{package}.domain",),
            allowed_groups=frozenset({"domain"}),
        ),
        ModuleGroup(
            name="application",
            module_prefixes=(f"{package}.application",),
            allowed_groups=frozenset({"application", "domain"}),
        ),
        ModuleGroup(
            name="inbound_adapter",
            module_prefixes=(f"{package}.cli", f"{package}.adapters.inbound"),
            allowed_groups=adapter_allowed,
        ),
        ModuleGroup(
            name="outbound_adapter",
            module_prefixes=(f"{package}.adapters.outbound",),
            allowed_groups=adapter_allowed,
        ),
        ModuleGroup(
            name="adapter",
            module_prefixes=(f"{package}.adapters",),
            allowed_groups=adapter_allowed,
        ),
        ModuleGroup(
            name="infrastructure",
            module_prefixes=_INFRASTRUCTURE_MODULES,
            allowed_groups=frozenset({"infrastructure"}),
        ),
    )


def default_policy() -> ArchitecturePolicy:
    """Return BeatCue's production architecture policy.

    Returns
    -------
    ArchitecturePolicy
        Configured policy for the ``beatcue`` package with the standard
        hexagonal groups from ``_beatcue_groups``.

    """
    return ArchitecturePolicy(groups=_beatcue_groups("beatcue"))


def fixture_policy(package: str) -> ArchitecturePolicy:
    """Return the generic fixture policy used by tests.

    Parameters
    ----------
    package
        Dotted fixture package name to classify.

    Returns
    -------
    ArchitecturePolicy
        Configured policy for ``package`` using the same group shape as
        ``_beatcue_groups(package)``.

    """
    return ArchitecturePolicy(groups=_beatcue_groups(package))
