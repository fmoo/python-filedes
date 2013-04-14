from setuptools import setup, Extension, find_packages
import imp
import os.path
import platform

LIBANCILLARY = ['ext/libancillary/' + p for p in ['fd_send.c', 'fd_recv.c']]
ANCILLARY = Extension('_ancillary', ['ext/ancillary.c'] + LIBANCILLARY)

PLATFORM_EXTENSIONS = {
    'Darwin': [Extension('_filedes', ['ext/posix_filedes.c',
                                      'ext/darwin_filedes.c'])] + [ANCILLARY],
    'Linux': [Extension('_filedes', ['ext/posix_filedes.c',
                                     'ext/linux_filedes.c'])] + [ANCILLARY],
}

ROOT = os.path.abspath(os.path.dirname(__file__))

def read(fname):
    """Read a file relative to the repository root"""
    return open(os.path.join(ROOT, fname)).read()

def version():
    """Return the version number from filedes/__version__.py"""
    file, pathname, description = imp.find_module('filedes', [ROOT])
    return imp.load_module('filedes', file, pathname, description).__version__

if __name__ == '__main__':
    VERSION = version()
    kwargs = dict(
        name='filedes',
        version=version(),
        description="Work with file descriptors in a more human way",
        long_description=read("README.rst"),
        packages=find_packages(exclude=['tests', 'tests.*']),
        author='Peter Ruibal',
        author_email='ruibalp@gmail.com',
        license='ISC',
        keywords='file-descriptor fd filedes',
        url='http://github.com/fmoo/python-filedes',
        download_url='https://github.com/fmoo/python-filedes'
                     '/archive/%s.tar.gz' % VERSION,

        classifiers=[
            "Development Status :: 4 - Beta",
            "License :: OSI Approved :: ISC License (ISCL)",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: POSIX :: Linux",
        ],

        install_requires=["unittest2"],
        setup_requires=['unittest2'],
        test_suite="tests",
    )

    # Add extension modules (as necessary)
    kwargs.update(dict(
        ext_modules=PLATFORM_EXTENSIONS.get(platform.system(), [])
    ))

    setup(**kwargs)
