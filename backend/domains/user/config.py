from dataclasses import dataclass


@dataclass(frozen=True)
class UserServiceConfig:

    signup_redirect_path: str
    client_origin: str = "http://localhost:5173"

    @property
    def signup_redirect_url(self) -> str:
        return f"{self.client_origin.rstrip('/')}{self.signup_redirect_path}"
