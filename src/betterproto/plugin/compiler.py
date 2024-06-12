import os.path
import sys

from .module_validation import ModuleValidator


try:
    # betterproto[compiler] specific dependencies
    import black
    import isort.api
    import jinja2
except ImportError as err:
    print(
        "\033[31m"
        f"Unable to import `{err.name}` from betterproto plugin! "
        "Please ensure that you've installed betterproto as "
        '`pip install "betterproto[compiler]"` so that compiler dependencies '
        "are included."
        "\033[0m"
    )
    raise SystemExit(1)

from .models import OutputTemplate


def outputfile_compiler(output_file: OutputTemplate) -> str:
    templates_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates")
    )

    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=jinja2.FileSystemLoader(templates_folder),
    )
    # Load the body first so we have a compleate list of imports needed.
    body_template = env.get_template("template.py.j2")
    header_template = env.get_template("header.py.j2")

    code = body_template.render(output_file=output_file)
    code = header_template.render(output_file=output_file) + code
    code = isort.api.sort_code_string(
        code=code,
        show_diff=False,
        py_version=37,
        profile="black",
        combine_as_imports=True,
        lines_after_imports=2,
        quiet=True,
        force_grid_wrap=2,
        known_third_party=["grpclib", "betterproto"],
    )
    code = black.format_str(
        src_contents=code,
        mode=black.Mode(),
    )

    # Validate the generated code.
    validator = ModuleValidator(iter(code.splitlines()))
    if not validator.validate():
        message_builder = ["[WARNING]: Generated code has collisions in the module:"]
        for collision, lines in validator.collisions.items():
            message_builder.append(f'  "{collision}" on lines:')
            for num, line in lines:
                message_builder.append(f"    {num}:{line}")
        print("\n".join(message_builder), file=sys.stderr)
    return code
