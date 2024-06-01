import pytest
import textwrap

from conan.internal.api.new.cmake_lib import source_cpp, source_h
from conan.internal.api.new.qbs_lib import qbs_file, conanfile_sources
from conan.test.utils.tools import TestClient
from jinja2 import Template


def gen_file(template, **context):
    t = Template(template)
    return t.render(**context)


@pytest.mark.tool("qbs")
def test_qbs_static_lib():
    client = TestClient()

    context = {
        "name": "hello",
        "version": "2.0",
        "package_name": "hello"
    }

    client.save({
        "conanfile.py": gen_file(conanfile_sources, **context),
        "hello.cpp": gen_file(source_cpp, **context),
        "hello.h": gen_file(source_h, **context),
        "hello.qbs": gen_file(qbs_file, **context),
    }, clean_first=True)

    client.run("create .")


@pytest.mark.tool("qbs")
def test_api_qbs_create_lib():
    client = TestClient()
    client.run("new qbs_lib -d name=hello -d version=1.0")
    client.run("create .")


@pytest.mark.tool("qbs")
def test_qbs_all_products():
    client = TestClient()

    context = {
        "name": "hello",
        "version": "2.0",
        "package_name": "hello"
    }

    conanfile = textwrap.dedent('''
    import os

    from conan import ConanFile, tools
    from conan.tools.qbs import Qbs
    from conan.tools.files import copy, collect_libs

    class Recipe(ConanFile):
        name = "hello"
        version = "1.0"

        exports_sources = "*.cpp", "*.h", "*.qbs"
        settings = "os", "compiler", "arch"

        def build(self):
            qbs = Qbs(self)
            qbs.profile = ""
            qbs.build_all()
        ''')

    client.save({
        "conanfile.py": conanfile,
        "hello.cpp": gen_file(source_cpp, **context),
        "hello.h": gen_file(source_h, **context),
        "hello.qbs": gen_file(qbs_file, **context),
    }, clean_first=True)

    client.run("create .")
    assert "--all-products" in client.out


@pytest.mark.tool("qbs")
def test_qbs_specific_products():
    client = TestClient()

    context = {
        "name": "hello",
        "version": "2.0",
        "package_name": "hello"
    }

    conanfile = textwrap.dedent('''
    import os

    from conan import ConanFile, tools
    from conan.tools.qbs import Qbs
    from conan.tools.files import copy, collect_libs

    class Recipe(ConanFile):
        name = "hello"
        version = "1.0"

        exports_sources = "*.cpp", "*.h", "*.qbs"
        settings = "os", "compiler", "arch"

        def build(self):
            qbs = Qbs(self)
            qbs.profile = ""
            qbs.build(products=["hello", "hello"])
        ''')

    client.save({
        "conanfile.py": conanfile,
        "hello.cpp": gen_file(source_cpp, **context),
        "hello.h": gen_file(source_h, **context),
        "hello.qbs": gen_file(qbs_file, **context),
    }, clean_first=True)

    client.run("create .")
    assert "--products hello,hello" in client.out