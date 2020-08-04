import os.path

try:
    # betterproto[compiler] specific dependencies
    import black
    import jinja2
except ImportError as err:
    missing_import = err.args[0][17:-1]
    print(
        "\033[31m"
        f"Unable to import `{missing_import}` from betterproto plugin! "
        "Please ensure that you've installed betterproto as "
        '`pip install "betterproto[compiler]"` so that compiler dependencies '
        "are included."
        "\033[0m"
    )
    raise SystemExit(1)

from betterproto.plugin.models import OutputTemplate

def outputfile_compiler(output_file: OutputTemplate) -> str:

    templates_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates")
    )

    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=jinja2.FileSystemLoader(templates_folder),
    )
    template = env.get_template("template.py.j2")


    res = black.format_str(
        template.render(output_file=output_file),
        mode=black.FileMode(target_versions={black.TargetVersion.PY37}),
    )

    return res
