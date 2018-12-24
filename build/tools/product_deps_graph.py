#!/usr/bin/env python

import json
import os
import sys

IGNORE_MODULE = ('libc', 'libc++', 'libm', 'libdl', 'libcutils',
                 'framework', 'ext', 'okhttp', 'core-oj', 'core-libart')
NONE_INSTALLED_CLASSES = (
    'STATIC_LIBRARIES', 'JAVA_LIBRARIES', 'HEADER_LIBRARIES', 'FAKE')


class Target(object):
    def __init__(self):
        self.arch = ""
        self.type = ""
        # Target installed path.
        self.target = ""


class Module(object):
    incremental = 0

    def __init__(self, product, name):
        self.id = Module.incremental
        Module.incremental = Module.incremental + 1
        self.product = product
        self.name = name
        self.path = ""
        self.targets = []
        self.depends = []

    @classmethod
    def reset(cls):
        cls.incremental = 0

    def parse_info(self, info):
        types = info['class']
        paths = info['installed']

        if len(types) == 0:
            print('Warning: module "{}" has no class defined.'.format(self.name))

        if not paths:
            name_ends_with_vendor = self.name.endswith('.vendor')
            # TODO: tidy the conditions.
            # if not name_ends_with_vendor and (len(types) != 1 or types[0] not in NONE_INSTALLED_CLASSES):
            #     print('Warning: {} has no target path'.format(self.name))
            #     return
            if not name_ends_with_vendor:
                print('Warning: {} has no target path'.format(self.name))
                return

        types = [t for t in types if t != 'STATIC_LIBRARIES']
        paths = [path.replace(self.product.product_out, '') for path in paths if not path.endswith(
            '.vdex') and not path.endswith('.odex')]
        # Remove leading '/'.
        paths = [path if not path.startswith(
            '/') else path[1:] for path in paths]

        # FIXME: why set path to the first element?
        self.path = info['path'][0] if info['path'] else None
        types_len = len(types)
        paths_len = len(paths)

        if types_len > 1 and paths_len != types_len:
            print('Warning: types > 1 and paths != types:\tname : {}\n\ttypes : {}\n\tpaths : {}\n'.format(
                self.name, types, paths))

        assert(types_len == 1 or paths_len == types_len)

        if types_len > 1:
            self.add_multi_targets(types, paths)
        elif types_len == 1:
            self.add_single_target(types, paths)

    def parse_depends(self, dependencies):
        '''
        Find and map all dependency module name to Module object.
        '''
        for dependency in dependencies:
            if dependency not in self.product.module_map:
                print('Warning: module "{}" has dependency "{}" but not defined in all module info.'.format(
                    self.name, dependency))
                continue
            if dependency in IGNORE_MODULE:
                continue
            dep_module = self.product.module_map[dependency]
            self.depends.append(dep_module)

    def get_arch(self, path, is_32_bit):
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

    def add_single_target(self, types, paths):
        '''Multiple target paths for one type'''
        is_32_bit = self.name.endswith('_32')

        for path in paths:
            target = Target()
            target.arch = self.get_arch(path, is_32_bit)
            target.type = types[0]
            target.target = path
            self.targets.append(target)

    def add_multi_targets(self, types, paths):
        '''Multiple target paths for multiple types'''
        for index in range(0, len(types)):
            path = paths[index]
            target = Target()
            # FIXME: use host_out to determine arch?
            target.arch = self.get_arch(
                path, path.startswith(self.product.host_out))
            target.type = types[index]
            target.target = path
            self.targets.append(target)


class Dependency(object):

    DIRECT_DEPENDS = 1
    INDIRECT_DEPENDS = 2
    BOTH_DEPENDS = DIRECT_DEPENDS | INDIRECT_DEPENDS

    def __init__(self, product):
        self.dependency_map = {}
        self.targets = {}  # A map from module name to Module object.
        self.module_map = product.module_map

    def add_depends_for_target(self, dependent_m):
        dependent_m_name = dependent_m.name
        self.targets[dependent_m_name] = dependent_m
        for dependency_m in dependent_m.depends:
            dependency_m_name = dependency_m.name
            self.targets[dependency_m_name] = dependency_m
            relation = Dependency.DIRECT_DEPENDS
            if (dependent_m_name, dependency_m_name) in self.dependency_map:
                relation = relation | self.dependency_map[(
                    dependent_m_name, dependency_m_name)]
            self.dependency_map[(
                dependent_m_name, dependency_m_name)] = relation
            self._add_indirect_depend(dependent_m, dependency_m)

    def _add_indirect_depend(self, dependent_m, dependency_m):
        for dependency_ind_m in dependency_m.depends:
            dependent_m_name = dependent_m.name
            dependency_ind_m_name = dependency_ind_m.name
            relation = Dependency.INDIRECT_DEPENDS
            if (dependent_m_name, dependency_ind_m_name) in self.dependency_map:
                relation = relation | self.dependency_map[(
                    dependent_m_name, dependency_ind_m_name)]
            self.dependency_map[(
                dependent_m_name, dependency_ind_m_name)] = relation


class Product(object):

    def __init__(self, prod_out_dir, filter_module_type, *args, **kwargs):
        self.prod_out_dir = prod_out_dir
        self.filter_module_type = filter_module_type
        self.module_map = {}

        self._load_prod_info()

    @property
    def product_out(self):
        return self.prod_info['product_out']

    @property
    def host_out(self):
        return self.prod_info['host_out']

    def parse(self):
        print('Parsing product out directory: {}'.format(self.prod_out_dir))
        self.parse_module_info()
        self.parse_module_depends()
        depends = self.parse_product()

        self.output_one_dot(depends)
        self.output_one_csv(depends)

    def parse_module_info(self):
        '''
        Generate a map with key is module name and value is Module object.
        '''
        module_info_json = os.path.join(self.prod_out_dir, 'module-info.json')
        with open(module_info_json, 'r') as f_module_info:
            root_module_info = json.load(f_module_info)

        for _, m_info in root_module_info.items():
            m_name = m_info['module_name']
            module = Module(self, m_name)
            module.parse_info(m_info)
            self.module_map[m_name] = module

    def parse_module_depends(self):
        module_deps_json = os.path.join(self.prod_out_dir, 'module-deps.json')
        with open(module_deps_json, 'r') as f_module_deps:
            root_module_deps = json.load(f_module_deps)

        for m_name, m_deps in root_module_deps.items():
            deps = m_deps['deps']
            if deps and m_name in self.module_map:
                module = self.module_map[m_name]
                module.parse_depends(deps)

    def parse_product(self):
        type_map = {
            'etc': 'ETC',
            'apk': 'APPS',
            'exe': 'EXECUTABLES',
            'test': 'NATIVE_TESTS',
        }
        dependency = Dependency(self)
        for package_name in self.prod_info["packages"]:
            if package_name not in self.module_map:
                print('Waring: package "{}" not defined in all module info.'.format(
                    package_name))
                continue
            module = self.module_map[package_name]
            for t in module.targets:
                if self.filter_module_type == 'all' or t.type == type_map[self.filter_module_type]:
                    dependency.add_depends_for_target(module)
        return dependency

    def output_one_dot(self, dependency):
        out_file_path = os.path.join(
            self.prod_out_dir, 'module-{}.dot'.format(self.filter_module_type))
        with open(out_file_path, 'w') as out_file:
            self.output_dot(out_file, dependency)

    def output_dot(self, out_file, dependency):
        targets = dependency.targets
        if not targets:
            return

        out_file.write('digraph {\n')
        out_file.write('graph [ ratio=.5 ];\n')

        for m_name, _ in sorted(targets.items()):
            out_file.write(
                '\t\"{0}\" [ label=\"{0}\" colorscheme=\"svg\" fontcolor=\"darkblue\" href=\"{0}\" ]\n'.format(m_name))

        dependency_map = dependency.dependency_map
        for k, relation in dependency_map.items():
            if relation == Dependency.DIRECT_DEPENDS:
                out_file.write('\t\"{}\" -> \"{}\"\n'.format(k[0], k[1]))

        out_file.write('}')

    def output_csv(self, file, file_deps, dependency):
        file.write('name,type,source-path,arch,host,installed-path\n')
        targets = dependency.targets

        for m_name, m in sorted(targets.items()):
            if m_name != m.name:
                print(
                    'Warning: module name and key in Dependency.targets map not consistent')
            for target in m.targets:
                # FIXME: host field is not target.type.
                file.write('{},{},{},{},{},{}\n'.format(
                    m_name, target.type, m.path, target.arch, target.type, target.target))

        file_deps.write('base,dependant\n')
        dependency_map = dependency.dependency_map

        for k, v in dependency_map.items():
            if (v & Dependency.DIRECT_DEPENDS) == Dependency.DIRECT_DEPENDS:
                file_deps.write('{},{}\n'.format(k[0], k[1]))

    def output_one_csv(self, depends):
        out_file_path = os.path.join(
            self.prod_out_dir, 'module-{}.csv'.format(self.filter_module_type))
        deps_out_file_path = os.path.join(
            self.prod_out_dir, 'depend-{}.csv'.format(self.filter_module_type))
        with open(out_file_path, 'w') as file:
            with open(deps_out_file_path, 'w') as file_deps:
                self.output_csv(file, file_deps, depends)

    def _load_prod_info(self):
        prod_info_json = os.path.join(self.prod_out_dir, 'product-info.json')
        with open(prod_info_json, 'r') as f_prod_info:
            self.prod_info = json.load(f_prod_info)


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
