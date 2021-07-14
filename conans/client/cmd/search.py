from collections import OrderedDict, namedtuple

from conans.errors import NotFoundException, RecipeNotFoundException
from conans.model.ref import ConanFileReference
from conans.search.search import (search_packages, search_recipes)


class Search(object):
    def __init__(self, cache, remote_manager, remotes):
        self._cache = cache
        self._remote_manager = remote_manager
        self._remotes = remotes

    def search_recipes(self, pattern, remote_name):
        references = OrderedDict()
        remote = self._remotes[remote_name]
        refs = self._remote_manager.search_recipes(remote, pattern)
        references[remote.name] = sorted(refs)
        return references

    remote_ref = namedtuple('remote_ref', 'ordered_packages')

    def search_packages(self, ref=None, remote_name=None, query=None):
        """ Return the single information saved in conan.vars about all the packages
            or the packages which match with a pattern

            Attributes:
                pattern = string to match packages
                remote_name = search on another origin to get packages info
                packages_pattern = String query with binary
                                   packages properties: "arch=x86 AND os=Windows"
        """
        if not remote_name:
            return self._search_packages_in_local(ref, query)

        if remote_name == 'all':
            return self._search_packages_in_all(ref, query)

        return self._search_packages_in(remote_name, ref, query)

    def _search_packages_in_local(self, ref=None, query=None):
        latest_rrev = self._cache.get_latest_rrev(ref)

        if not latest_rrev:
            raise RecipeNotFoundException(ref)

        conanfileref = latest_rrev
        package_layouts = []
        pkg_ids = self._cache.get_package_ids(conanfileref)
        for pkg in pkg_ids:
            latest_prev = self._cache.get_latest_prev(pkg)
            package_layouts.append(self._cache.pkg_layout(latest_prev))

        packages_props = search_packages(package_layouts, query)
        ordered_packages = OrderedDict(sorted(packages_props.items()))

        references = OrderedDict()
        references[None] = self.remote_ref(ordered_packages)
        return references

    def _search_packages_in_all(self, ref=None, query=None):
        references = OrderedDict()
        # We have to check if there is a remote called "all"
        # Deprecate: 2.0 can remove this check
        if 'all' not in self._remotes:
            for remote in self._remotes.values():
                try:
                    packages_props = self._remote_manager.search_packages(remote, ref, query)
                    if packages_props:
                        ordered_packages = OrderedDict(sorted(packages_props.items()))
                        references[remote.name] = self.remote_ref(ordered_packages)
                except NotFoundException:
                    continue
            return references

        return self._search_packages_in('all', ref, query)

    def _search_packages_in(self, remote_name, ref=None, query=None):
        remote = self._remotes[remote_name]
        packages_props = self._remote_manager.search_packages(remote, ref, query)
        ordered_packages = OrderedDict(sorted(packages_props.items()))
        references = OrderedDict()
        references[remote.name] = self.remote_ref(ordered_packages)
        return references
