#!/usr/bin/env python
# -*- coding: utf8 -*-
import setuptools
from setuptools.command.develop import develop
from setuptools.command.install import install


class DevelopScript(develop):
    def run(self):
        develop.run(self)
        ntlk_install_packages()


class InstallScript(install):
    def run(self):
        install.run(self)
        ntlk_install_packages()


def ntlk_install_packages():
    import nltk
    print("Downloading nltk packages...")
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

setuptools.setup(
    name="zeeguu_core",
    version="0.1",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    author="Zeeguu Team",
    author_email="me@mir.lu",
    description="Core for Zeeguu",
    keywords="second language acquisition api",
    cmdclass={
        'develop': DevelopScript,
        'install': InstallScript,
    },
)