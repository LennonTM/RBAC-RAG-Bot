from dataclasses import dataclass


READ_GENERAL = "read:general"
READ_ENGINEERING = "read:engineering"
READ_FINANCE = "read:finance"
READ_HR = "read:hr"
READ_MARKETING = "read:marketing"

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "general": frozenset({READ_GENERAL}),
    "engineering": frozenset({READ_GENERAL, READ_ENGINEERING}),
    "finance": frozenset({READ_GENERAL, READ_FINANCE}),
    "hr": frozenset({READ_GENERAL, READ_HR}),
    "marketing": frozenset({READ_GENERAL, READ_MARKETING}),
    "system_admin": frozenset(
        {
            READ_GENERAL,
            READ_ENGINEERING,
            READ_FINANCE,
            READ_HR,
            READ_MARKETING,
        }
    ),
}


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    role: str
    permissions: frozenset[str]

    @property
    def resource_scopes(self) -> frozenset[str]:
        return frozenset(permission.removeprefix("read:") for permission in self.permissions)


def user_for(username: str, role: str) -> AuthenticatedUser:
    permissions = ROLE_PERMISSIONS.get(role)
    if permissions is None:
        raise ValueError(f"Unknown role: {role}")
    return AuthenticatedUser(username, role, permissions)
