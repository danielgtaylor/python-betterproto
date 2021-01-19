import os.path

import black
import jinja2

from .models import OutputTemplate


def outputfile_compiler(output_file: OutputTemplate, line_length: int = black.DEFAULT_LINE_LENGTH) -> str:

    templates_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates")
    )

    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=jinja2.FileSystemLoader(templates_folder),
    )
    template = env.get_template("template.py.j2")

    return black.format_str(
        template.render(output_file=output_file),
        mode=black.Mode(line_length=line_length, target_versions={black.TargetVersion.PY37}),
    )
