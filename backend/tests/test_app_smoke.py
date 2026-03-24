from app.main import create_app


def test_create_app_exposes_fastapi_metadata():
    app = create_app()

    assert app.title == "Paper API"
    assert app.version
