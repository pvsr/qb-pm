from pathlib import Path
from typing import Optional

from qbpm import profiles
from qbpm.profiles import Profile


def check_is_empty(path: Path):
    assert len(list(path.iterdir())) == 0


def check_empty_profile(profile: Optional[Profile]):
    assert profile
    config_dir = profile.root / "config"
    assert list(profile.root.iterdir()) == [config_dir]
    assert list(config_dir.iterdir()) == []


def check_new_profile(profile: Profile):
    assert profile
    config_dir = profile.root / "config"
    assert list(profile.root.iterdir()) == [config_dir]
    assert list(config_dir.iterdir()) == [config_dir / "config.py"]


def test_set_profile(tmp_path: Path):
    assert Profile("test", tmp_path).root == tmp_path / "test"


def test_create_profile(tmp_path: Path):
    profile = Profile("test", tmp_path)
    assert profiles.create_profile(profile)
    assert list(tmp_path.iterdir()) == [profile.root]
    check_empty_profile(profile)


def test_create_profile_conflict(tmp_path: Path):
    (tmp_path / "test").touch()
    profile = Profile("test", tmp_path)
    assert not profiles.create_profile(profile)


def test_create_profile_parent(tmp_path: Path):
    profile = Profile("../test", tmp_path / "profiles")
    assert not profiles.create_profile(profile)
    assert not (tmp_path / "test").exists()


def test_create_profile_nested_conflict(tmp_path: Path):
    assert profiles.create_profile(Profile("test", tmp_path))
    assert not profiles.create_profile(Profile("test/a", tmp_path))


def test_create_config(tmp_path: Path):
    profile = Profile("test", tmp_path)
    config_dir = profile.root / "config"
    config_dir.mkdir(parents=True)
    profiles.create_config(profile)
    assert list(config_dir.iterdir()) == [config_dir / "config.py"]


def test_overwrite_config(tmp_path: Path):
    profile = Profile("test", tmp_path)
    url = "http://example.com"
    config_dir = profile.root / "config"
    config_dir.mkdir(parents=True)
    profiles.create_config(profile)
    profiles.create_config(profile, url, True)
    assert list(config_dir.iterdir()) == [config_dir / "config.py"]
    with (config_dir / "config.py").open() as conf:
        for line in conf:
            if url in line:
                return
    raise AssertionError()


def test_ensure_profile_exists_exists(tmp_path: Path):
    profile = Profile("test", tmp_path)
    profile.root.mkdir()
    assert profiles.ensure_profile_exists(profile, False)
    assert profiles.ensure_profile_exists(profile, True)
    check_is_empty(profile.root)


def test_ensure_profile_exists_does_not_exist(tmp_path: Path):
    assert not profiles.ensure_profile_exists(Profile("test", tmp_path), False)
    check_is_empty(tmp_path)


def test_ensure_profile_exists_not_dir(tmp_path: Path):
    profile = Profile("test", tmp_path)
    profile.root.touch()
    assert not profiles.ensure_profile_exists(profile, False)
    assert not profiles.ensure_profile_exists(profile, True)


def test_ensure_profile_exists_create(tmp_path: Path):
    profile = Profile("test", tmp_path)
    assert profiles.ensure_profile_exists(profile, True)
    check_new_profile(profile)


def test_new_profile(tmp_path: Path):
    profile = Profile("test", tmp_path)
    assert profiles.new_profile(profile)
    check_new_profile(profile)
