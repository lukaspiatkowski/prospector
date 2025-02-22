from mypy import api

from prospector.message import Location, Message
from prospector.tools import ToolBase

__all__ = ("MypyTool",)

from prospector.tools.exceptions import BadToolConfig

LIST_OPTIONS = ["allow", "check", "disallow", "no-check", "no-warn", "warn"]
VALID_OPTIONS = LIST_OPTIONS + [
    "strict",
    "follow-imports",
    "ignore-missing-imports",
    "implicit-optional",
    "strict-optional",
    "platform",
    "python-2-mode",
    "python-version",
    "namespace-packages",
]


def format_message(message):
    try:
        (path, line, char, err_type, err_msg) = message.split(":", 4)
        line = int(line)
        character = int(char)
    except ValueError:
        try:
            (path, line, err_type, err_msg) = message.split(":", 3)
            line = int(line)
            character = None
        except ValueError:
            (path, err_type, err_msg) = message.split(":", 2)
            line = 0
            character = None
    location = Location(
        path=path,
        module=None,
        function=None,
        line=line,
        character=character,
    )
    return Message(
        source="mypy",
        code=err_type.lstrip(" "),
        location=location,
        message=err_msg.lstrip(" "),
    )


class MypyTool(ToolBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checker = api
        self.options = ["--show-column-numbers", "--no-error-summary"]

    def configure(self, prospector_config, _):
        options = prospector_config.tool_options("mypy")

        for option_key in options.keys():
            if option_key not in VALID_OPTIONS:
                url = "https://github.com/PyCQA/prospector/blob/master/prospector/tools/mypy/__init__.py"
                raise BadToolConfig(
                    "mypy", f"Option {option_key} is not valid. " f"See the list of possible options: {url}"
                )

        strict = options.get("strict", False)

        follow_imports = options.get("follow-imports", "normal")
        ignore_missing_imports = options.get("ignore-missing-imports", False)
        implict_optional = options.get("implict-optional", False)
        platform = options.get("platform", None)
        python_2_mode = options.get("python-2-mode", False)
        python_version = options.get("python-version", None)
        strict_optional = options.get("strict-optional", False)
        namespace_packages = options.get("namespace-packages", False)

        self.options.append(f"--follow-imports={follow_imports}")

        if strict:
            self.options.append("--strict")

        if ignore_missing_imports:
            self.options.append("--ignore-missing-imports")

        if implict_optional:
            self.options.append("--implict-optional")

        if platform:
            self.options.append(f"--platform {platform}")

        if python_2_mode:
            self.options.append("--py2")

        if python_version:
            self.options.append(f"--python-version {python_version}")

        if strict_optional:
            self.options.append("--strict-optional")

        if namespace_packages:
            self.options.append("--namespace-packages")

        for list_option in LIST_OPTIONS:
            for entry in options.get(list_option, []):
                self.options.append(f"--{list_option}-{entry}")

    def run(self, found_files):
        paths = [str(path) for path in found_files.python_modules]
        paths.extend(self.options)
        result = self.checker.run(paths)
        report, _ = result[0], result[1:]  # noqa

        return [format_message(message) for message in report.splitlines()]
