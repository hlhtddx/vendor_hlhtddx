#!/usr/bin/env python

import json
import os
import sys

IGNORED_MODULES = ('libc', 'libc++', 'libm', 'libdl', 'libcutils',
                   'framework', 'ext', 'okhttp', 'core-oj', 'core-libart')

# WARN: some module with class is SHARED_LIBRARIES also has no installed path.
# Currently found these module's key always ends with `.vendor` or `.vendor_32`.
NONE_INSTALLED_CLASSES = (
    'STATIC_LIBRARIES', 'JAVA_LIBRARIES', 'HEADER_LIBRARIES', 'FAKE')


class Target(object):
    def __init__(self):
        self.arch = ''
        self.clazz = ''
        self.installed_path = ''


class Module(object):
    def __init__(self, product, key):
        self.product = product
        self.key = key
        self.path = ''
        self.targets = []
        self.dependencies = []

    def parse_info(self, info):
        classes = info['class']
        installed_paths = info['installed']

        if not classes:
            print('Warning: module "{}" has no class defined.'.format(self.key))
            return

        if not installed_paths and not self._is_ignoring_zero_installed_path(info):
            print('Warning: module {} has no installed path'.format(self.key))
            return

        valid_classes = [
            c for c in classes if c not in ['STATIC_LIBRARIES']]
        valid_installed_paths = [self._normalizing_installed_path(
            p) for p in installed_paths if not self._is_ignoring_installed_path(p)]

        if not info['path']:
            print('Warning: module "{}" without source path.'.format(self.key))
        else:
            # A small part of modules defined with more than one Android.mk or
            # Android.bp, so they have more than one source path. Here we just
            # choose the first one until we have better choice.
            self.path = info['path'][0]

        valid_classes_len = len(valid_classes)
        valid_paths_len = len(valid_installed_paths)

        # Here we try to make sure one class mapped to one installed path.
        if valid_paths_len != valid_classes_len:
            print('Warning: valid classes length: {} != valid installed path length: {}, module: {}'.format(
                self.key, valid_classes_len, valid_paths_len))
            print('\tclasses: {}'.format(valid_classes))
            print('\tinstalled paths: {}\n'.format(valid_installed_paths))
        assert(valid_classes_len == 1 or valid_classes_len == valid_paths_len)

        if valid_classes_len > 1:
            self._add_multiple_targets(valid_classes, valid_installed_paths)
        elif valid_classes_len == 1:
            self._add_single_target(valid_classes[0], valid_installed_paths)

    def parse_dependencies(self, dependencies):
        '''
        Find and map all dependency module name to Module object.python argparse
        '''
        for dependency in dependencies:
            if dependency not in self.product.module_map:
                print(
                    'Warning: module "{}" has dependency "{}", but dependency not in module-info.json.'.format(self.key, dependency))
                continue
            if dependency in IGNORED_MODULES:
                continue
            self.dependencies.append(self.product.module_map[dependency])

    def _get_arch(self, path, is_32_bit):
        if path.startswith(self.product.host_out):
            if(is_32_bit):
                return "host32"
            else:
                return "host64"
        else:
            if(is_32_bit):
                return "target32"
            else:
                return "target64"

    def _add_single_target(self, clazz, paths):
        '''
        Multiple installed path for single class.
        '''
        for path in paths:
            target = Target()
            target.arch = self._get_arch(path, self.key.endswith('_32'))
            target.clazz = clazz
            target.installed_path = path
            self.targets.append(target)

    def _add_multiple_targets(self, classes, paths):
        '''
        Multiple installed paths for multiple classes.
        '''
        for i, v in enumerate(classes):
            path = paths[i]
            target = Target()
            # FIXME: use host_out to determine arch?
            target.arch = self._get_arch(
                path, path.startswith(self.product.host_out))
            target.clazz = v
            target.installed_path = path
            self.targets.append(target)

    def _is_ignoring_zero_installed_path(self, info):
        if self.key.endswith('.vendor') or self.key.endswith('.vendor_32'):
            return True
        for c in info['class']:
            if c not in NONE_INSTALLED_CLASSES:
                return False
        return True

    def _is_ignoring_installed_path(self, path):
        _, ext = os.path.splitext(path)
        return ext in ['.vdex', '.odex']

    def _normalizing_installed_path(self, path):
        path.replace(self.product.product_out, '')
        if path.startswith('/'):
            path = path[1:]
        return path


class Dependency(object):

    DIRECT_DEPENDS = 1
    INDIRECT_DEPENDS = 2
    BOTH_DEPENDS = DIRECT_DEPENDS | INDIRECT_DEPENDS

    def __init__(self, product):
        self.dependency_map = {}
        self.targets = {}  # A map from module key to Module object.
        self.module_map = product.module_map

    def add_depends_for_target(self, dependent_m):
        dependent_m_key = dependent_m.key
        self.targets[dependent_m_key] = dependent_m
        for dependency_m in dependent_m.dependencies:
            dependency_m_key = dependency_m.key
            self.targets[dependency_m_key] = dependency_m
            relation = Dependency.DIRECT_DEPENDS
            if (dependent_m_key, dependency_m_key) in self.dependency_map:
                relation = relation | self.dependency_map[(
                    dependent_m_key, dependency_m_key)]
            self.dependency_map[(
                dependent_m_key, dependency_m_key)] = relation
            self._add_indirect_depend(dependent_m, dependency_m)

    def _add_indirect_depend(self, dependent_m, dependency_m):
        for dependency_ind_m in dependency_m.dependencies:
            dependent_m_key = dependent_m.key
            dependency_ind_m_key = dependency_ind_m.key
            relation = Dependency.INDIRECT_DEPENDS
            if (dependent_m_key, dependency_ind_m_key) in self.dependency_map:
                relation = relation | self.dependency_map[(
                    dependent_m_key, dependency_ind_m_key)]
            self.dependency_map[(
                dependent_m_key, dependency_ind_m_key)] = relation


class Product(object):
    def __init__(self, prod_out_dir, filter_module_type, *args, **kwargs):
        self.prod_out_dir = prod_out_dir
        self.filter_module_type = filter_module_type
        self.module_map = {}

    @property
    def product_out(self):
        '''
        Get product build output directory. Usually defined by
        $ANDROID_PRODUCT_OUT environment variable.

        E.g. `out/target/product/generic_arm6`.
        '''
        return self.prod_info['product_out']

    @property
    def host_out(self):
        '''
        Get host build output directory. Usually defined by $ANDROID_HOST_OUT
        environment variable.
        '''
        return self.prod_info['host_out']

    def parse(self):
        print('Parsing product, out directory is: {}'.format(self.prod_out_dir))
        self.prod_info = self._load_data_file('product-info.json')
        self._parse_module_info()
        self._parse_module_dependencies()
        depends = self.parse_product()

        self._output_one_dot(depends)
        self._output_one_csv(depends)

    def _parse_module_info(self):
        '''
        Parse file `module-info.json` and generate a map with key is module key
        and value is Module object.

        Note:
        - Each Module has a module key and module name. Module key is unique
        but module name is not.
        - Different Android versions have different Module fields.
        usually new Android version has more fields within Module object.
        '''
        modules_info = self._load_data_file('module-info.json')
        for m_key, m_info in modules_info.items():
            module = Module(self, m_key)
            module.parse_info(m_info)
            self.module_map[m_key] = module

    def _parse_module_dependencies(self):
        '''
        Parse file `module-deps.json`.
        '''
        module_deps = self._load_data_file('module-deps.json')
        for m_key, m_deps in module_deps.items():
            if m_key not in self.module_map:
                print(
                    'Warning: module "{}" in module-deps.json but not in module-info.json.'.format(m_key))
                continue
            if m_deps['deps']:
                module = self.module_map[m_key]
                module.parse_dependencies(m_deps['deps'])

    def parse_product(self):
        class_map = {
            'etc': 'ETC',
            'apk': 'APPS',
            'exe': 'EXECUTABLES',
            'test': 'NATIVE_TESTS',
        }
        dependency = Dependency(self)
        for pkg_name in self.prod_info["packages"]:
            if pkg_name not in self.module_map:
                print(
                    'Warning: product package "{}" not defined in module-info.json.'.format(pkg_name))
                continue
            module = self.module_map[pkg_name]
            for t in module.targets:
                if self.filter_module_type == 'all' or t.clazz == class_map[self.filter_module_type]:
                    dependency.add_depends_for_target(module)
        return dependency

    def _output_one_dot(self, dependency):
        out_file_path = os.path.join(
            self.prod_out_dir, 'module-{}.dot'.format(self.filter_module_type))
        with open(out_file_path, 'w') as out_file:
            self._output_dot(out_file, dependency)

    def _output_dot(self, out_file, dependency):
        targets = dependency.targets
        if not targets:
            return

        out_file.write('digraph {\n')
        out_file.write('graph [ ratio=.5 ];\n')

        for m_key, _ in sorted(targets.items()):
            out_file.write(
                '\t\"{0}\" [ label=\"{0}\" colorscheme=\"svg\" fontcolor=\"darkblue\" href=\"{0}\" ]\n'.format(m_key))

        dependency_map = dependency.dependency_map
        # k is a tuple of (dependent, dependency).
        for k, relation in dependency_map.items():
            if relation == Dependency.DIRECT_DEPENDS:
                out_file.write('\t\"{}\" -> \"{}\"\n'.format(k[0], k[1]))

        out_file.write('}')

    def _output_csv(self, file, file_deps, dependency):
        file.write('name,class,source-path,arch,host,installed-path\n')
        targets = dependency.targets

        for m_key, m in sorted(targets.items()):
            if m_key != m.key:
                print(
                    'Warning: module key not equals key in Dependency.targets map.')
            for target in m.targets:
                # FIXME: host field is not target.clazz.
                file.write('{},{},{},{},{},{}\n'.format(
                    m_key, target.clazz, m.path, target.arch, target.clazz, target.installed_path))

        file_deps.write('base,dependant\n')
        dependency_map = dependency.dependency_map

        # k is a tuple of (dependent, dependency).
        for k, v in dependency_map.items():
            if (v & Dependency.DIRECT_DEPENDS) == Dependency.DIRECT_DEPENDS:
                file_deps.write('{},{}\n'.format(k[0], k[1]))

    def _output_one_csv(self, depends):
        out_file_path = os.path.join(
            self.prod_out_dir, 'module-{}.csv'.format(self.filter_module_type))
        deps_out_file_path = os.path.join(
            self.prod_out_dir, 'depend-{}.csv'.format(self.filter_module_type))
        with open(out_file_path, 'w') as file:
            with open(deps_out_file_path, 'w') as file_deps:
                self._output_csv(file, file_deps, depends)

    def _load_data_file(self, filename):
        '''
        Load json data file from product output directory and return a Python
        object instance.
        '''
        with open(os.path.join(self.prod_out_dir, filename), 'r') as f:
            return json.load(f)


def parse_options(args):
    import argparse
    parser = argparse.ArgumentParser(
        description='Product dependency relationship graph generator.')
    parser.add_argument('-c', type=str, dest='prod_out_dir',
                        help='Specify android product out directory, default is $ANDROID_PRODUCT_OUT.')
    parser.add_argument('-t', type=str, dest='filter_type', choices=['all', 'exe', 'apk', 'etc', 'test'], default='all',
                        help='Specify filter module type, default is "all".')

    args = parser.parse_args(args)

    if not args.prod_out_dir:
        args.prod_out_dir = os.environ.get('ANDROID_PRODUCT_OUT', None)
    if args.prod_out_dir is None:
        parser.error(
            'Environment variable $ANDROID_PRODUCT_OUT or parameter "-c" should be provided.')

    return args


def main():
    options = parse_options(sys.argv[1:])
    product = Product(options.prod_out_dir, options.filter_type)
    product.parse()


if __name__ == '__main__':
    main()
