from collections import defaultdict, namedtuple
import pathlib

import archpkg

def get_dependency_map(depman, mods):
  map = defaultdict(set)
  rmap = defaultdict(set)

  for name, mod in mods.items():
    depends = getattr(mod, 'depends', ())

    ds = [depman.get(d) for d in depends]
    for d in ds:
      rmap[d.pkgname].add(name)

  for name, ds in map.items():
    dependers = rmap[name]
    for dd in dependers:
      map[dd].update(ds)

  return map

_DependencyTuple = namedtuple(
  '_DependencyTuple', 'pkgdir pkgname')

class Dependency(_DependencyTuple):
  _has_resolved = False

  def resolve(self):
    if self._has_resolved:
      return self._resolved

    try:
      r = self._find_local_package()
    except FileNotFoundError:
      r = None
    self._has_resolved = True
    self._resolved = r
    return r

  def _find_local_package(self):
    files = [x for x in self.pkgdir.iterdir()
              if x.name.endswith('.pkg.tar.xz')]
    pkgs = []
    for x in files:
      info = archpkg.PkgNameInfo.parseFilename(x.name)
      if info.name == self.pkgname:
        pkgs.append(x)

    if len(pkgs) == 1:
      return pkgs[0]
    elif not pkgs:
      raise FileNotFoundError
    else:
      ret = sorted(
        pkgs, reverse=True, key=lambda x: x.stat().st_mtime)[0]
      return ret

class DependencyManager:
  _CACHE = {}

  def __init__(self, repodir):
    self.repodir = pathlib.Path(repodir)

  def get(self, what):
    if isinstance(what, tuple):
      pkgbase, pkgname = what
    else:
      pkgbase = pkgname = what

    if pkgname not in self._CACHE:
      self._CACHE[pkgname] = Dependency(
        self.repodir / pkgbase, pkgname)
    return self._CACHE[pkgname]
