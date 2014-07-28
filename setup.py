from distutils.core import setup

setup(
    name='tornado-smtpclient',
    version='0.1.0',
    packages=['tornado', 'tornado.smtp'],
    url='https://github.com/vuamitom/tornado-smtpclient',
    license='',
    author='tamvu',
    keywords = ["tornado", "smtp", "email", "client", "non blocking", "async"],
    author_email='vumhtam@gmail.com',
    description='A non-blocking smtp client to work with tornado-based application',
    install_requires=['tornado'],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Communications :: Email :: Email Clients (MUA)',

        # Pick your license as you wish (should match "license" above)
        # 'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
