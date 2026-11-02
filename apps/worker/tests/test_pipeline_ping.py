from indexbeef_vision.pipeline import VERSAO_PIPELINE, ping


def test_ping_ok() -> None:
    r = ping()
    assert r["status"] == "ok"
    assert r["pipeline"] == VERSAO_PIPELINE
