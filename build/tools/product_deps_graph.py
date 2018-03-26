#!/usr/bin/env python

import json
import os
import sys

result_type = "all"
file_dir = os.environ["ANDROID_PRODUCT_OUT"]

class Target:
    def __init__(self):
        self.arch = ""
        self.type = ""
        self.target = ""

class Module:
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

    def getArch(self, path, is32Bit):
        if path.startswith(self.product.host_out):
            if(is32Bit):
                return "host32"
            else:
                return "host64"
        else:
            if(is32Bit):
                return "target32"
            else:
                return "target64"

    def addSingleTarget(self, types, paths):
        '''Multiple target paths for one type'''
        is32Bit = False
        if self.name.endswith('_32'): #32bit modules
            is32Bit = True

        for path in paths:
            target = Target()
            target.arch = self.getArch(path, is32Bit)
            target.type = types[0]
            target.target = path
            self.targets.append(target)

    def addMultiTargets(self, types, paths):
        '''Multiple target paths for multiple types'''
        for index in range(0, len(types)):
            path = paths[index]
            target = Target()
            target.arch = self.getArch(path, path.startswith(self.product.host_out))
            target.type = types[index]
            target.target = path
            self.targets.append(target)

    def parse(self, module):
        types = [type for type in module['class'] if not (type == 'STATIC_LIBRARIES')]
        paths = [path.replace(self.product.product_out, '') for path in module['installed']]

        if len(paths) == 0:
            sys.stderr.write("Warning: %s has no target path\n" % self.name)
            return

        self.path = module['path']

        dump_module = False
        if len(types) > 1:
            sys.stderr.write('Warning: types > 1:\n')
            dump_module = True

        if len(paths) != len(types):
            sys.stderr.write('Warning: paths != types:\n')
            dump_module = True

        if dump_module:
            sys.stderr.write('\tname : %s\n\ttypes : %s\n\tpaths : %s\n' % (self.name, types, paths))
        
        assert(len(types) == 1 or len(paths) == len(types))

        if len(types) == 1:
            self.addSingleTarget(types, paths)
        else:
            self.addMultiTargets(types, paths)

    def parseDepends(self, dependencies):
        for dependant in dependencies:
            if not self.product.module_map.has_key(dependant):
                continue
            if dependant in Product.ignore_module:
                continue

            dep_module = self.product.module_map[dependant]
            self.depends.append(dep_module)


class Dependency:

    DIRECT_DEPENDS = 1
    INDIRECT_DEPENDS = 2
    BOTH_DEPENDS = DIRECT_DEPENDS | INDIRECT_DEPENDS
    
    def __init__(self, product):
        self.dependency_map = {}
        self.targets = {}
        self.module_map = product.module_map

    def addDependsForTarget(self, base):
        name = base.name
        self.targets[name] = base
        for dep_module in base.depends:
            dependant = dep_module.name
            self.targets[dependant] = dep_module
            relation = Dependency.DIRECT_DEPENDS
            if (self.dependency_map.has_key((name, dependant))):
                relation = relation | self.dependency_map[(name, dependant)]
            self.dependency_map[(name, dependant)] = relation
            self.addIndirectDepend(base, dep_module)

    def addIndirectDepend(self, base, dep_module):
        for depends_ind in dep_module.depends:
            name = base.name
            dname = depends_ind.name
            relation = Dependency.INDIRECT_DEPENDS
            if (self.dependency_map.has_key((name, dname))):
                relation = relation | self.dependency_map[(name, dname)]
            self.dependency_map[(name, dname)] = relation

class Product:
    def __init__(self, file_dir):
        self.file_dir = file_dir

        f_product_info = open('%s%sproduct-info.json' % (self.file_dir, os.sep), mode = "r")
        self.root_product_info = json.load(f_product_info)
        f_product_info.close()

        self.product_out = self.root_product_info['product_out'] + '/'
        self.host_out = self.root_product_info['host_out'] + '/'

    ignore_module = ('libc', 'libc++', 'libm', 'libdl', 'libcutils', 'framework', 'ext', 'okhttp', 'core-oj', 'core-libart')

    def outputDot(self, file, depends):
        targets = depends.targets

        file.write('digraph {\n')
        file.write('graph [ ratio=.5 ];\n')
        if (len(targets) == 0):
            return

        k = targets.keys()
        k.sort()
        for m in k:
            try:
                file.write('\t\"%s\" [ label=\"%s\" colorscheme=\"svg\" fontcolor=\"darkblue\" href=\"%s\" ]\n'
                    % (m, m, m))
            except KeyError as err:
                sys.stderr.write('outputDot error: "%s"\n' % err.message)
        dependency_map = depends.dependency_map
        p = dependency_map.keys()
        for (m, d) in p:
            if(dependency_map[(m, d)] == 1):
                file.write('\t\"%s\" -> \"%s\"\n' % (m, d))

        file.write('}')

    def outputOneDot(self, depends):
        file = open('%s%smodule-%s.dot' % (self.file_dir, os.sep, result_type), 'w')
        self.outputDot(file, depends)
        file.close()

    def outputCsv(self, file, file_deps, depends):
        file.write('name,type,source-path,arch,host,installed-path\n')
        targets = depends.targets
        k = targets.keys()
        k.sort()
        for key in k:
            module = targets[key]
            name = module.name
            for target in module.targets:
                file.write('%s,%s,%s,%s,%s,%s\n' % (name, target.type, module.path, target.arch, target.type, target.target))

        file_deps.write('base,dependant\n')
        dependency_map = depends.dependency_map
        k = dependency_map.keys()
        for d in k:
            try:
                v = dependency_map[d]
                if(v == 1):
                    file_deps.write('%s,%s\n' % (d))
            except KeyError as err:
                sys.stderr.write('outputCsv error: "%s"\n' % err.message)

    def outputOneCsv(self, depends):
        file = open('%s%smodule-%s.csv' % (self.file_dir, os.sep, result_type), 'w')
        file_deps = open('%s%sdepend-%s.csv' % (self.file_dir, os.sep, result_type), 'w')
        self.outputCsv(file, file_deps, depends)
        file_deps.close()
        file.close()

    def paserModules(self):
        f_module_info = open('%s%smodule-info.json' % (self.file_dir, os.sep), mode = "r")
        root_module_info = json.load(f_module_info)
        f_module_info.close()

        self.module_map = {}

        k = root_module_info.keys()
        for name in k:
            module = Module(self, name)
            module.parse(root_module_info[name])
            self.module_map[name] = module

    def parseDepends(self):
        f_module_deps = open('%s%smodule-deps.json' % (self.file_dir, os.sep), mode = "r")
        root_module_deps = json.load(f_module_deps)
        f_module_deps.close()
        k = root_module_deps.keys()
        for name in k:
            base = root_module_deps[name]
            dependencies = base['deps']
            if len(dependencies) > 0 and self.module_map.has_key(name):
                module = self.module_map[name]
                module.parseDepends(dependencies)

    def parseProduct(self):
        packages = self.root_product_info["packages"]

        depends = Dependency(self)

        for package_name in packages:
            if(not self.module_map.has_key(package_name)):
                continue

            module = self.module_map[package_name]
            for t in module.targets:
                if (result_type == 'etc' and t.type != 'ETC'):
                    continue
                elif (result_type == 'app' and t.type != 'APPS'):
                    continue
                elif (result_type == 'exe' and t.type != 'EXECUTABLES'):
                    continue
                elif (result_type == 'test' and t.type != 'NATIVE_TESTS'):
                    continue
                depends.addDependsForTarget(module)

        return depends

    def parse(self, file_dir):
        self.paserModules()
        self.parseDepends()
        depends = self.parseProduct()
        
        self.outputOneDot(depends)
        self.outputOneCsv(depends)

def parse_options():
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-c':
            i = i + 1
            file_dir = sys.argv[i]
        elif sys.argv[i] == '-t':
            i = i + 1
            result_type = sys.argv[i]

def main():
    if(__name__ == '__main__') :
        parse_options()

        if(file_dir == ''):
            sys.stderr.write('Source directory MUST be set by argument or $ANDROID_PRODUCT_OUT!\n')
            return -1

        sys.stderr.write('Parsing directory "%s"\n' % file_dir)
        p = Product(file_dir)
        p.parse(file_dir)

    return 0

main()
