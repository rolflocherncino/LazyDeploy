from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
     name='lazydeploy',  
     version='0.2',
     scripts=['lazy'] ,
     author="Rolf Locher",
     author_email="rolf.locher@ncino.com",
     description="A SFDX utility package",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/rolflocherncino/LazyDeploy",
     packages=find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3"
     ],
     setup_requires=['wheel']
 )