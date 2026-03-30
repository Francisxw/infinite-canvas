from app.config import Settings


def test_settings_accepts_comma_separated_allowed_origins(monkeypatch) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "http://localhost:15191,http://127.0.0.1:15191",
    )

    settings = Settings()

    assert settings.allowed_origins == [
        "http://localhost:15191",
        "http://127.0.0.1:15191",
    ]


def test_settings_accepts_json_allowed_origins(monkeypatch) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        '["http://localhost:15191","http://127.0.0.1:15191"]',
    )

    settings = Settings()

    assert settings.allowed_origins == [
        "http://localhost:15191",
        "http://127.0.0.1:15191",
    ]


def test_settings_accepts_empty_allowed_origins(monkeypatch) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", "")

    settings = Settings()

    assert settings.allowed_origins == []
