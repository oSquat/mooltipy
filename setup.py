
from setuptools import setup, find_packages

setup(
    name = 'mooltipy',
    version = '1.0.0',
    description = 'Mooltipass command line utilities and development library.',
    url = 'https://github.com/osquat/mooltipy',
    author = 'Vic Simeone',
    author_email = 'mooltipy@osquat.com',
    license = 'GPLv3+',
    keywords = ['mooltipass'],
    classifiers = [
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Operating System :: POSIX :: Linux',
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: End Users/Desktop',
    ],
    packages = find_packages(),
    install_requires = ['pycrypto>=2.6.1', 'pyusb>=1.0.0b2'],
    entry_points = {
        'console_scripts': [
            'mooltipy = mooltipy.utilities.mooltipy_wrapper:main',
            'mpdata = mooltipy.utilities.mpdata:main',
            'mplogin = mooltipy.utilities.mplogin:main',
            'mpfavorites = mooltipy.utilities.mpfavorites:main',
            'mpparams = mooltipy.utilities.mpparams:main',
        ],
    }
)
