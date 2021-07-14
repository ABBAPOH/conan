import textwrap
from collections import OrderedDict

import pytest

from conans.test.utils.tools import TestClient, TestServer


class TestSearch:

    @pytest.fixture
    def remotes(self):
        self.servers = OrderedDict()
        self.servers["remote1"] = TestServer(server_capabilities=[])
        self.servers["remote2"] = TestServer(server_capabilities=[])

        self.client = TestClient(servers=self.servers)

    def test_search_no_params(self):
        self.servers = OrderedDict()
        self.client = TestClient(servers=self.servers)

        self.client.run("search", assert_error=True)
        assert "error: the following arguments are required: query" in self.client.out

    def test_search_no_matching_recipes(self, remotes):
        expected_output = ("remote1:\n"
                           "  There are no matching recipes\n"
                           "remote2:\n"
                           "  There are no matching recipes\n")

        self.client.run("search whatever")
        assert expected_output == self.client.out

    def test_search_no_configured_remotes(self):
        self.servers = OrderedDict()
        self.client = TestClient(servers=self.servers)

        self.client.run("search whatever", assert_error=True)
        assert "ERROR: The remotes registry is empty" in self.client.out

    def test_search_disabled_remote(self, remotes):
        self.client.run("remote disable remote1")
        self.client.run("search whatever -r remote1", assert_error=True)
        assert "ERROR: Remote 'remote1' is disabled" in self.client.out


class TestRemotes:

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.servers = OrderedDict()
        self.users = {}
        self.client = TestClient()

    def _add_remote(self, remote_name):
        self.servers[remote_name] = TestServer(users={"user": "passwd"})
        self.users[remote_name] = [("user", "passwd")]
        self.client = TestClient(servers=self.servers, users=self.users)

    def _add_recipe(self, remote, reference):
        conanfile = textwrap.dedent("""
            from conans import ConanFile
            class MyLib(ConanFile):
                pass
            """)

        self.client.save({'conanfile.py': conanfile})
        self.client.run("export . {}".format(reference))
        self.client.run("upload --force -r {} {}".format(remote, reference))

    def test_no_remotes(self):
        self.client.run("search something", assert_error=True)
        expected_output = "The remotes registry is empty. Please add at least one valid remote"
        assert expected_output in self.client.out

    def test_search_by_name(self):
        remote_name = "remote1"
        recipe_name = "test_recipe/1.0.0@user/channel"
        self._add_remote(remote_name)
        self._add_recipe(remote_name, recipe_name)

        self.client.run("search -r {} {}".format(remote_name, "test_recipe"))

        expected_output = (
            "remote1:\n"
            "  test_recipe\n"
            "    {}\n".format(recipe_name)
        )

        assert expected_output == self.client.out

    def test_search_in_all_remotes(self):
        remote1 = "remote1"
        remote2 = "remote2"

        remote1_recipe1 = "test_recipe/1.0.0@user/channel"
        remote1_recipe2 = "test_recipe/1.1.0@user/channel"
        remote2_recipe1 = "test_recipe/2.0.0@user/channel"
        remote2_recipe2 = "test_recipe/2.1.0@user/channel"

        expected_output = (
            "remote1:\n"
            "  test_recipe\n"
            "    test_recipe/1.0.0@user/channel\n"
            "    test_recipe/1.1.0@user/channel\n"
            "remote2:\n"
            "  test_recipe\n"
            "    test_recipe/2.0.0@user/channel\n"
            "    test_recipe/2.1.0@user/channel\n"
        )

        self._add_remote(remote1)
        self._add_recipe(remote1, remote1_recipe1)
        self._add_recipe(remote1, remote1_recipe2)

        self._add_remote(remote2)
        self._add_recipe(remote2, remote2_recipe1)
        self._add_recipe(remote2, remote2_recipe2)

        self.client.run("search test_recipe")
        assert expected_output == self.client.out

    def test_search_in_one_remote(self):
        remote1 = "remote1"
        remote2 = "remote2"

        remote1_recipe1 = "test_recipe/1.0.0@user/channel"
        remote1_recipe2 = "test_recipe/1.1.0@user/channel"
        remote2_recipe1 = "test_recipe/2.0.0@user/channel"
        remote2_recipe2 = "test_recipe/2.1.0@user/channel"

        expected_output = (
            "remote1:\n"
            "  test_recipe\n"
            "    test_recipe/1.0.0@user/channel\n"
            "    test_recipe/1.1.0@user/channel\n"
        )

        self._add_remote(remote1)
        self._add_recipe(remote1, remote1_recipe1)
        self._add_recipe(remote1, remote1_recipe2)

        self._add_remote(remote2)
        self._add_recipe(remote2, remote2_recipe1)
        self._add_recipe(remote2, remote2_recipe2)

        self.client.run("search -r remote1 test_recipe")
        assert expected_output in self.client.out

    def test_search_package_found_in_one_remote(self):

        remote1 = "remote1"
        remote2 = "remote2"

        remote1_recipe1 = "test_recipe/1.0.0@user/channel"
        remote1_recipe2 = "test_recipe/1.1.0@user/channel"
        remote2_recipe1 = "another_recipe/2.0.0@user/channel"
        remote2_recipe2 = "another_recipe/2.1.0@user/channel"

        expected_output = (
            "remote1:\n"
            "  test_recipe\n"
            "    test_recipe/1.0.0@user/channel\n"
            "    test_recipe/1.1.0@user/channel\n"
            "remote2:\n"
            "  There are no matching recipes\n"
        )

        self._add_remote(remote1)
        self._add_recipe(remote1, remote1_recipe1)
        self._add_recipe(remote1, remote1_recipe2)

        self._add_remote(remote2)
        self._add_recipe(remote2, remote2_recipe1)
        self._add_recipe(remote2, remote2_recipe2)

        self.client.run("search test_recipe")
        assert expected_output == self.client.out

    def test_search_in_missing_remote(self):
        remote1 = "remote1"

        remote1_recipe1 = "test_recipe/1.0.0@user/channel"
        remote1_recipe2 = "test_recipe/1.1.0@user/channel"

        expected_output = "No remote 'wrong_remote' defined in remotes"

        self._add_remote(remote1)
        self._add_recipe(remote1, remote1_recipe1)
        self._add_recipe(remote1, remote1_recipe2)

        self.client.run("search -r wrong_remote test_recipe", assert_error=True)
        assert expected_output in self.client.out

    def test_search_wildcard(self):
        remote1 = "remote1"

        remote1_recipe1 = "test_recipe/1.0.0@user/channel"
        remote1_recipe2 = "test_recipe/1.1.0@user/channel"
        remote1_recipe3 = "test_another/2.1.0@user/channel"
        remote1_recipe4 = "test_another/4.1.0@user/channel"

        expected_output = (
            "remote1:\n"
            "  test_another\n"
            "    test_another/2.1.0@user/channel\n"
            "    test_another/4.1.0@user/channel\n"
            "  test_recipe\n"
            "    test_recipe/1.0.0@user/channel\n"
            "    test_recipe/1.1.0@user/channel\n"
        )

        self._add_remote(remote1)
        self._add_recipe(remote1, remote1_recipe1)
        self._add_recipe(remote1, remote1_recipe2)
        self._add_recipe(remote1, remote1_recipe3)
        self._add_recipe(remote1, remote1_recipe4)

        self.client.run("search test_*")
        assert expected_output in self.client.out
