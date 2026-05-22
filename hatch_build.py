import shutil
import sys
from pathlib import Path
from py_compile import PycInvalidationMode, compile as compile_pyc

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name != "wheel":
            return

        if sys.implementation.name != "cpython":
            raise RuntimeError("Bytecode-only wheels must be built with CPython.")

        if sys.version_info < (3, 12):
            raise RuntimeError("This project requires Python >= 3.12 to build bytecode-only wheels.")

        source_package = Path(self.root, "src", "zworkflow")
        build_package = Path(self.root, "build", "pyc-wheel", "zworkflow")

        if build_package.exists():
            shutil.rmtree(build_package)

        for source_file in source_package.rglob("*.py"):
            relative_path = source_file.relative_to(source_package)
            bytecode_file = build_package / relative_path.with_suffix(".pyc")
            bytecode_file.parent.mkdir(parents=True, exist_ok=True)

            compile_pyc(
                str(source_file),
                cfile=str(bytecode_file),
                dfile=str(Path("zworkflow") / relative_path),
                doraise=True,
                invalidation_mode=PycInvalidationMode.UNCHECKED_HASH,
            )

        build_data["force_include"][str(build_package)] = "zworkflow"
        build_data["tag"] = f"cp{sys.version_info.major}{sys.version_info.minor}-none-any"
