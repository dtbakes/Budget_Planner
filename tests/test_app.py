from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "streamlit_app.py")


def test_app_runs_and_flags_overspending():
    at = AppTest.from_file(APP).run()
    assert not at.exception
    assert at.metric[0].value == "$5,000"
    assert not at.error

    at.sidebar.number_input[0].set_value(3000).run()
    assert at.metric[2].value.startswith("-$")
    assert "over budget" in at.error[0].value
