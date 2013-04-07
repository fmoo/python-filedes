from setuptools import setup, Extension
import platform

LIBANCILLIARY = ['ext/libancilliary/' + p for p in ['fd_send.c', 'fd_recv.c']]

PLATFORM_EXTENSIONS = {
    'Darwin': [Extension('_filedes', ['ext/darwin_filedes.c'] + LIBANCILLIARY)],
    'Linux': [Extension('_filedes', ['ext/linux_filedes.c'] + LIBANCILLIARY)],
}

if __name__ == '__main__':
    kwargs = dict(
        name='filedes',
        version='0.1',
        description="Work with file descriptors in a more human way",
        packages=['filedes'],
        author='Peter Ruibal',
        author_email='ruibalp@gmail.com',
        license='ISC',
        keywords='file-descriptor fd filedes',
        url='http://github.com/fmoo/python-filedes',

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
