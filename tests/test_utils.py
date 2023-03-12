import contextlib

import pytest

from doru.manager.utils import rollback


def readline(path: str):
    with open(path, "r") as f:
        return f.readline()


@pytest.fixture
def tmpfile(tmpdir):
    return tmpdir.mkdir("tmp").join("test.txt")


class SampleClass:
    foo = "foo"
    bar = "bar"

    def __init__(self, path: str) -> None:
        self.path = path
        with open(self.path, "w") as f:
            f.write("line")

    def _change_propeties_and_files(self) -> None:
        self.foo = "newfoo"
        self.bar = "newbar"
        with open(self.path, "w") as f:
            f.write("newline")

    @rollback(properties=["foo", "bar"], files=["path"])
    def good_method_1(self):
        self._change_propeties_and_files()

    @rollback(properties=["foo"], files=["path"])
    def good_method_2(self):
        self._change_propeties_and_files()

    @rollback(properties=[], files=[])
    def good_method_3(self):
        self._change_propeties_and_files()

    @rollback(properties=["hoge"], files=[])
    def good_method_4(self):
        self._change_propeties_and_files()

    @rollback(properties=[], files=["hoge"])
    def good_method_5(self):
        self._change_propeties_and_files()

    @rollback(properties=["foo", "bar"], files=["path"])
    def bad_method_1(self):
        self._change_propeties_and_files()
        raise Exception

    @rollback(properties=["foo"], files=["path"])
    def bad_method_2(self):
        self._change_propeties_and_files()
        raise Exception

    @rollback(properties=[], files=[])
    def bad_method_3(self):
        self._change_propeties_and_files()
        raise Exception

    @rollback(properties=["hoge"], files=[])
    def bad_method_4(self):
        self._change_propeties_and_files()
        raise Exception

    @rollback(properties=[], files=["hoge"])
    def bad_method_5(self):
        self._change_propeties_and_files()
        raise Exception


def test_rollback_with_good_method(tmpfile):
    sample1 = SampleClass(tmpfile)
    sample1.good_method_1()
    assert sample1.foo == "newfoo"
    assert sample1.bar == "newbar"
    assert readline(sample1.path) == "newline"

    sample2 = SampleClass(tmpfile)
    sample2.good_method_2()
    assert sample2.foo == "newfoo"
    assert sample2.bar == "newbar"
    assert readline(sample2.path) == "newline"

    sample3 = SampleClass(tmpfile)
    sample3.good_method_3()
    assert sample3.foo == "newfoo"
    assert sample3.bar == "newbar"
    assert readline(sample3.path) == "newline"

    sample4 = SampleClass(tmpfile)
    with pytest.raises(AttributeError):
        sample4.good_method_4()

    sample5 = SampleClass(tmpfile)
    with pytest.raises(AttributeError):
        sample5.good_method_5()

    # When the source file to backup doesn't exist
    sample6 = SampleClass(tmpfile)
    with pytest.raises(FileNotFoundError):
        sample6.path = "dummy.txt"
        sample6.good_method_1()


def test_rollback_with_bad_method(tmpfile):
    sample1 = SampleClass(tmpfile)
    with contextlib.suppress(Exception):
        sample1.bad_method_1()
    assert sample1.foo == "foo"
    assert sample1.bar == "bar"
    assert readline(sample1.path) == "line"

    sample2 = SampleClass(tmpfile)
    with contextlib.suppress(Exception):
        sample2.bad_method_2()
    assert sample2.foo == "foo"
    assert sample2.bar == "newbar"  # sample2.bar is not marked to rollback
    assert readline(sample2.path) == "line"

    sample3 = SampleClass(tmpfile)
    with contextlib.suppress(Exception):
        sample3.bad_method_3()
    assert sample3.foo == "newfoo"
    assert sample3.bar == "newbar"
    assert readline(sample3.path) == "newline"

    sample4 = SampleClass(tmpfile)
    with pytest.raises(AttributeError):
        sample4.bad_method_4()

    sample5 = SampleClass(tmpfile)
    with pytest.raises(AttributeError):
        sample5.bad_method_5()

    sample6 = SampleClass(tmpfile)
    with pytest.raises(FileNotFoundError):
        sample6.path = "dummy.txt"
        sample6.bad_method_1()
