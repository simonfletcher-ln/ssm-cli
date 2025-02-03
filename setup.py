from setuptools import setup, find_packages

setup(
    name='ssm-cli',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        "boto3",
        "inquirer"
    ],
    entry_points={
        'console_scripts': [
            'ssm=ssm_cli.cli:cli',  # Adjust this to your main module and function
        ],
    },
    author='Simon Fletcher',
    author_email='simon.fletcher@lexisnexisrisk.com',
    description='A brief description of your project',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/ssm-cli',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6'
)