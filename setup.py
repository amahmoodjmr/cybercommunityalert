from setuptools import setup, find_packages

setup(
    name='community_cyber_alert',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # List your project's dependencies here
        'flask',
        'sqlalchemy',
        # Add other dependencies as needed
    ],
)
