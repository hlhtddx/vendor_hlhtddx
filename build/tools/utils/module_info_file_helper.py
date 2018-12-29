'''
Helper functions for debugging file module-info.json.
'''
import json
import os
import sys


class ModuleInfoFileHelper(object):
    def __init__(self, data_file):
        self.modules_info = {}
        self._load_file(data_file)

    def dump_unique_classes(self):
        classes = self.get_unique_classes()
        for c in classes:
            print(c)

    def get_unique_classes(self):
        classes = {}
        for info in self.modules_info.values():
            for c in info['class']:
                classes[c] = True

        return [k for k in classes.keys()]

    def check_classes(self):
        '''
        Print debug information if the size of module's class not equals to 1.
        '''
        for m_key, info in self.modules_info.items():
            if len(info['class']) != 1:
                print('module: {}, class: {}'.format(m_key, info['class']))

    def check_no_installed(self):
        '''
        Print debug information if module has no installed path.
        '''
        no_installed_classes = {}
        for m_key, info in self.modules_info.items():
            if not info['installed']:
                print('module: {}, info: {}'.format(m_key, info))
                for c in info['class']:
                    no_installed_classes[c] = True

        print('None installed classes: {}'.format([k for k in no_installed_classes.keys()]))

    def check_path(self):
        '''
        Print debug information if the size of module's path not equals to 1.
        '''
        for m_key, info in self.modules_info.items():
            if len(info['path']) != 1:
                print('module: {}, path: {}'.format(m_key, info['path']))

    def _load_file(self, data_file):
        with open(data_file, 'r') as f:
            self.modules_info = json.load(f)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Helper functions for parsing file module-info.json.')
    parser.add_argument('datafile', help='data file for parsing')
    parser.add_argument('--func', help='specify function to run',
                        required=True,
                        choices=(
                            'unique_classes',
                            'check_classes',
                            'check_no_installed',
                            'check_path',
                        ))

    args = parser.parse_args()

    if not os.path.isfile(args.datafile):
        print('Data file "{}" is not exists or not a file.'.format(args.datafile))
        sys.exit(1)

    m_helper = ModuleInfoFileHelper(args.datafile)

    if args.func == 'unique_classes':
        m_helper.dump_unique_classes()

    elif args.func == 'check_classes':
        m_helper.check_classes()

    elif args.func == 'check_no_installed':
        m_helper.check_no_installed()

    elif args.func == 'check_path':
        m_helper.check_path()
