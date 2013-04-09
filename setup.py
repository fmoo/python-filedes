from setuptools import setup, Extension, find_packages
import platform

LIBANCILLARY = ['ext/libancillary/' + p for p in ['fd_send.c', 'fd_recv.c']]
ANCILLARY = Extension('_ancillary', ['ext/ancillary.c'] + LIBANCILLARY)

PLATFORM_EXTENSIONS = {
    'Darwin': [Extension('_filedes', ['ext/darwin_filedes.c'])] + [ANCILLARY],
    'Linux': [Extension('_filedes', ['ext/linux_filedes.c'])] + [ANCILLARY],
}

if __name__ == '__main__':
    kwargs = dict(
        name='filedes',
        version='0.1',
        description="Work with file descriptors in a more human way",
        packages=find_packages(exclude=['tests', 'tests.*']),
        author='Peter Ruibal',
        author_email='ruibalp@gmail.com',
        license='ISC',
        keywords='file-descriptor fd filedes',
        url='http://github.com/fmoo/python-filedes',

        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: ISC License (ISCL)",
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
