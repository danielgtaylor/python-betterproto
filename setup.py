from setuptools import setup, find_packages

setup(
    name="betterproto",
    version="1.2.5",
    description="A better Protobuf / gRPC generator & library",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="http://github.com/danielgtaylor/python-betterproto",
    author="Daniel G. Taylor",
    author_email="danielgtaylor@gmail.com",
    license="MIT",
    entry_points={
        "console_scripts": ["protoc-gen-python_betterproto=betterproto.plugin:main"]
    },
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "output", "output.*"]
    ),
    package_data={"betterproto": ["py.typed", "templates/template.py.j2"]},
    python_requires=">=3.6",
    install_requires=[
        'dataclasses; python_version<"3.7"',
        'backports-datetime-fromisoformat; python_version<"3.7"',
        "grpclib",
        "stringcase",
    ],
    extras_require={"compiler": ["black", "jinja2", "protobuf"]},
    zip_safe=False,
)
