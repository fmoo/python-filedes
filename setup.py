from setuptools import setup, Extension
import platform

PLATFORM_EXTENSIONS = {
    'Darwin': [Extension('_fdinfo', ['ext/darwin_fdinfo.c'])]
}

if __name__ == '__main__':
    kwargs = dict(
        name='fdinfo',
        version='0.1',
        py_modules=['fdinfo'],
    )

    # Add extension modules (as necessary)
    kwargs.update(dict(
        ext_modules=PLATFORM_EXTENSIONS.get(platform.system(), [])
    ))

    setup(**kwargs)
