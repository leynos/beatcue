"""Read a parsed workflow as text, for the clauses that search values.

The walk turns every key and scalar into one line, and the computed-secret
reader judges that text; the rules decide what each finding means.
"""

from __future__ import annotations

import re


def _lines(value: object) -> list[str]:
    """Return the keys and scalars of ``value``, depth first, one per entry."""
    if value is None:
        return []
    if isinstance(value, dict):
        return [
            line
            for key, item in value.items()
            for line in [f"{' '.join(_lines(key))}:", *_lines(item)]
        ]
    if isinstance(value, list):
        return [line for item in value for line in _lines(item)]
    if isinstance(value, bool):
        return [str(value).lower()]
    return [str(value)]


def rendered(value: object) -> str:
    """Return every key and scalar in a parsed value, one per line.

    Reading the parse rather than the file is deliberate: comments are gone,
    so prose explaining why the token is absent does not read as the token
    being present, while a block scalar's content, which Actions expands, is
    read in full. It reaches every place a value can sit, at workflow, job or
    step scope, in a ``run`` body, an action input, an ``env`` value, an ``if:``,
    a ``defaults.run.shell`` or a ``secrets:`` forwarding or declaration,
    without a clause having to be told about each. Keys carry their ``:`` so the
    computed-secret clause can tell a ``secrets:`` key from an expression.
    """
    return "".join(f"{line}\n" for line in _lines(value))


_SECRETS_WORD = re.compile(r"(?<![A-Za-z0-9_.])secrets(?![A-Za-z0-9_])")


def computes_a_secret(text: str) -> bool:
    """Return whether ``text`` reaches the ``secrets`` context other than by name.

    ``secrets['CS_' + ...]``, ``secrets[format(...)]`` and ``toJSON(secrets)``
    all hand a step the token without spelling it, so a search for the name
    passes them. Every ``secrets`` word is judged by what follows it: ``.`` is a
    named reference, which the name search judges, and ``:`` is a YAML key,
    which the job clauses judge. Anything else is refused.
    """
    for match in _SECRETS_WORD.finditer(text):
        following = text[match.end() :].lstrip()
        if following and not _names_or_declares(following[0]):
            return True
    return False


def _names_or_declares(character: str) -> bool:
    """Return whether a character after ``secrets`` makes it a name or a key.

    ``.`` starts a named reference and ``:`` a YAML key; an identifier character
    after whitespace means the word was prose.
    """
    return character in ".:" or (
        character.isascii() and (character.isalnum() or character == "_")
    )
