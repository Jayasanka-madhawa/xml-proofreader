from xml_proofreader import config, llm


def test_model_comes_from_config_json():
    assert llm.MODEL == config.load()["model"]


def test_value_in_file_replaces_the_default(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"model": "another-model"}')
    assert config.load(path)["model"] == "another-model"


def test_missing_file_uses_the_default(tmp_path):
    assert config.load(tmp_path / "missing.json") == config.DEFAULTS
