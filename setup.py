from setuptools import setup, find_packages

setup(
    name="betterproto",
    version="1.1.0",
    description="A better Protobuf / gRPC generator & library",
    long_description=open("README.md", "r").read(),
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
    package_data={"betterproto": ["py.typed", "templates/template.py"]},
    python_requires=">=3.7",
    install_requires=["grpclib", "stringcase"],
    extras_require={"compiler": ["jinja2", "protobuf"]},
    zip_safe=False,
)
