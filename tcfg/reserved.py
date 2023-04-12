from __future__ import annotations


__all__ = [
    "MISSING",
    "TypePath",
]


class Missing:
    """Placeholding for missing values. Allows for null values to be
    represented as literals.
    """


MISSING = Missing()


class TypePath(str):
    """Allows for eazy path generation."""

    def __init__(self, *paths: str, strip: bool = True) -> None:
        self.path = TypePath.normalize(
            *paths, strip=strip) if len(paths) > 0 else ""

    @staticmethod
    def normalize(*paths: str, strip: bool = True) -> str:
        """Normalize a path or segments of a path into a consistant path with
        `\\` replaced with `/` and either leading and trailing `/` stripped or
        left alone.
        """

        if strip:
            return "/".join(
                path.replace("\\", "/").strip("/")
                for path in paths
            )

        return "/".join(
            [
                paths[1].lstrip("/"),
                *[
                    path.replace("\\", "/").strip("/")
                    for path in paths[1:-1]
                ],
                paths[-1].lstrip("/")
            ]
        )

    def __truediv__(self, scalar: TypePath):
        if isinstance(scalar, TypePath):
            return TypePath(self.path.rstrip("/") + "/" + scalar.path.lstrip("/"))
        raise TypeError("Can't divide with values other that 'Path'")

    def __repr__(self) -> str:
        return f"Path({self.path!r})"

    def __str__(self) -> str:
        return self.path
