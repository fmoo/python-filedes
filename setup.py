from setuptools import setup, Extension
import platform

PLATFORM_EXTENSIONS = {
    'Darwin': [Extension('_fdinfo', ['ext/darwin_fdinfo.c'])],
    'Linux': [Extension('_fdinfo', ['ext/linux_fdinfo.c'])],
}

if __name__ == '__main__':
    kwargs = dict(
        name='fdinfo',
        version='0.1',
        description="Work with file descriptors in a more human way",
        py_modules=['fdinfo'],
        author='Peter Ruibal',
        author_email='ruibalp@gmail.com',
        license='ISC',
        keywords='file-descriptor',
        url='http://github.com/fmoo/python-fdinfo',

        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: ISC License (ISCL)",
        ],
    )

    # Add extension modules (as necessary)
    kwargs.update(dict(
        ext_modules=PLATFORM_EXTENSIONS.get(platform.system(), [])
    ))

    setup(**kwargs)
