#!/usr/bin/env python

import json
import os
import sys

class AndroidModule:
    def __init__(self):
        self.name = ""
        self.arch = ""
        self.type = ""
        self.target = ""
        self.depends = ""

class AndroidProduct:
    def __init__(self, file_dir):
        f_module_info = open('%s%smodule-info.json' % (file_dir, os.sep), mode = "r")
        f_module_deps = open('%s%smodule-deps.json' % (file_dir, os.sep), mode = "r")
        f_product_info = open('%s%sproduct-info.json' % (file_dir, os.sep), mode = "r")
        self.root_module_info = json.load(f_module_info)
        self.root_module_deps = json.load(f_module_deps)
        self.root_product_info = json.load(f_product_info)

        self.product_out = self.root_product_info['product_out'] + '/'
        self.host_out = self.root_product_info['host_out'] + '/'

        self.targets_etc = {}
        self.depends_etc = {}

        self.targets_apk = {}
        self.depends_apk = {}

        self.targets_exe = {}
        self.depends_exe = {}

        self.targets_test = {}
        self.depends_test = {}

        self.targets = {}
        self.depends = {}

    ignore_module = ('libc', 'libc++', 'libm', 'libdl', 'libcutils', 'framework', 'ext', 'okhttp', 'core-oj', 'core-libart')

    def addIndirectDepend(self, depends, base, dependant):
        try:
            indirect_dependants = self.root_module_deps[dependant]
            for indirect_dependant in indirect_dependants['deps']:
                if (depends.has_key((base, indirect_dependant))):
                    depends[(base, indirect_dependant)] = depends[(base, indirect_dependant)] | 2
                else:
                    depends[(base, indirect_dependant)] = 2 #indirect dependency
        except KeyError:
            sys.stderr.write("Module %s is not found\n" % dependant)

    def addDirectDepend(self, targets, depends, name, module):
        try:
            dependants = self.root_module_deps[name]
            targets[name] = 1
            for dependant in dependants['deps']:

                if not self.root_module_info.has_key(dependant):
                    continue
                if len(self.root_module_info[dependant]['installed']) == 0:
                    continue
                if dependant in AndroidProduct.ignore_module:
                    continue
                    
                targets[dependant] = 1
                if (depends.has_key((name, dependant))):
                    depends[(name, dependant)] = depends[(name, dependant)] | 1
                else:
                    depends[(name, dependant)] = 1
                self.addIndirectDepend(depends, name, dependant)
        except KeyError:
            sys.stderr.write("Module %s is not found\n" % name)

    def outputDot(self, file, targets, depends):
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

        p = depends.keys()
        for (m, d) in p:
            if(depends[(m, d)] == 1):
                file.write('\t\"%s\" -> \"%s\"\n' % (m, d))

        file.write('}')

    def outputOneDot(self, file_dir, type, targets, depends):
        file = open('%s%smodule-%s.dot' % (file_dir, os.sep, type), 'w')
        self.outputDot(file, targets, depends)
        file.close()

    def outputAllDot(self, file_dir):
        self.outputOneDot(file_dir, 'apk', self.targets_apk, self.depends_apk)
        self.outputOneDot(file_dir, 'exe', self.targets_exe, self.depends_exe)
        self.outputOneDot(file_dir, 'etc', self.targets_etc, self.depends_etc)
        self.outputOneDot(file_dir, 'test', self.targets_test, self.depends_test)
        self.outputOneDot(file_dir, 'all', self.targets, self.depends)

    def outputCsv(self, file, file_deps, targets, depends):
        file.write('name,type,source-path,install-path\n')
        k = targets.keys()
        k.sort()
        for m in k:
            try:
                module = self.root_module_info[m]
                types = module['class']
                paths = module['installed']
                if len(types) != len(paths):
                    sys.stderr.write("len(types) != len(paths), Module name=%s, types=%s, paths=%s\n" % (m, types, paths))
                    assert(len(types) == len(paths) or len(types) == 1)
                for index in range(0, len(types)):
                    file.write('%s,%s,%s,%s\n' % (m, types[index], module['path'][0], paths[index]))
            except KeyError as err:
                sys.stderr.write('outputCsv error: "%s"\n' % err.message)

        file_deps.write('base,dependant\n')
        k = depends.keys()
        for d in k:
            try:
                v = depends[d]
                if(v == 1):
                    file_deps.write('%s,%s\n' % (d))
            except KeyError as err:
                sys.stderr.write('outputCsv error: "%s"\n' % err.message)
            

    def outputOneCsv(self, file_dir, type, targets, depends):
        file = open('%s%smodule-%s.csv' % (file_dir, os.sep, type), 'w')
        file_deps = open('%s%sdepend-%s.csv' % (file_dir, os.sep, type), 'w')
        self.outputCsv(file, file_deps, targets, depends)
        file_deps.close()
        file.close()

    def outputAllCsv(self, file_dir):
        self.outputOneCsv(file_dir, 'apk', self.targets_apk, self.depends_apk)
        self.outputOneCsv(file_dir, 'exe', self.targets_exe, self.depends_exe)
        self.outputOneCsv(file_dir, 'etc', self.targets_etc, self.depends_etc)
        self.outputOneCsv(file_dir, 'test', self.targets_test, self.depends_test)
        self.outputOneCsv(file_dir, 'all', self.targets, self.depends)

    def removeUselessTarget(self):
        k = self.root_module_info.keys()
        for m in k:
            module = self.root_module_info[m]

            types = [type for type in module['class'] if not (type == 'STATIC_LIBRARIES')]
            paths = [path.replace(self.product_out, '') for path in module['installed']]

            if len(paths) == 0:
                self.root_module_info.pop(m)
                continue

            dump_module = False                
            if len(types) > 1:
                sys.stderr.write('Warning: types > 1:\n')
                dump_module = True

            if len(paths) != len(types):
                sys.stderr.write('Warning: paths != types:\n')
                dump_module = True

            if dump_module:
                sys.stderr.write('\tname : %s\n\ttypes : %s\n\tpaths : %s\n' % (m, types, paths))
            
            assert(len(types) == 1 or len(paths) == len(types))

            module['class'] = types
            module['installed'] = paths

    def parse(self, file_dir):

        self.removeUselessTarget()
        packages = self.root_product_info["packages"]

        for package_name in packages:
            if(not self.root_module_info.get(package_name)):
                continue

            if package_name in AndroidProduct.ignore_module:
                continue

            m = self.root_module_info[package_name]
            classtype = m['class'][0]

            if (classtype == 'ETC'):
                self.addDirectDepend(self.targets_etc, self.depends_etc, package_name, m)
            elif (classtype == 'APPS'):
                self.addDirectDepend(self.targets_apk, self.depends_apk, package_name, m)
            elif (classtype == 'EXECUTABLES'):
                self.addDirectDepend(self.targets_exe, self.depends_exe, package_name, m)
            elif (classtype == 'NATIVE_TESTS'):
                self.addDirectDepend(self.targets_test, self.depends_test, package_name, m)

            self.addDirectDepend(self.targets, self.depends, package_name, m)
        
        self.outputAllDot(file_dir)
        self.outputAllCsv(file_dir)
        

def main():
    if(__name__ == '__main__') :
        file_dir = ""

        if ( len(sys.argv) > 1) :
            file_dir = sys.argv[1]
        else:
            file_dir = os.environ["ANDROID_PRODUCT_OUT"]

        if(file_dir == ''):
            sys.stderr.write('Source directory MUST be set by argument or $ANDROID_PRODUCT_OUT!\n')
            return -1

        sys.stderr.write('Parsing directory "%s"\n' % file_dir)
        p = AndroidProduct(file_dir)
        p.parse(file_dir)

    return 0

main()
