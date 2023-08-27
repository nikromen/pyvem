"""
Wrapper for executing shell commands.
"""

import logging
import sys
from dataclasses import dataclass
from io import TextIOWrapper
from os import getcwd
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Optional, TextIO

from pyvem.constants import FAILURE, SUCCESS
from pyvem.exceptions import PyVemException

logger = logging.getLogger(__name__)


@dataclass
class CmdResult:
    retval: int
    stdout: str = ""
    stderr: str = ""

    @property
    def stderr_and_stdout(self) -> str:
        result = ""
        if self.stdout:
            result += self.stdout

        if not self.stderr:
            return result

        if result:
            result += "\n"

        result += self.stderr
        return result


class Cmd:
    def __init__(self, cwd: Path = Path(getcwd())) -> None:
        self.cwd = cwd

    @staticmethod
    def _tee_process_output(process: Popen, tee_to_stdout: bool, stdout: bool) -> str:
        output = process.stdout if stdout else process.stderr
        if output is None:
            return ""

        print_output = sys.stdout if stdout else sys.stderr

        # TODO: how to capture colors?
        captured_output = ""
        for out_line in TextIOWrapper(output, encoding="utf-8"):  # type: ignore
            captured_output += out_line

            if tee_to_stdout:
                print(out_line, file=print_output, end="")

        return captured_output

    def _prepare_process(
        self,
        arguments: list[str],
        context: Optional[Path],
        use_venv: bool,
        **popen_kwargs,
    ) -> Popen:
        if context is not None:
            cmd_context = context
        else:
            cmd_context = self.cwd

        logger.debug(
            f"Running command: $ {' '.join(arguments)}; in context {cmd_context}"
        )

        stdout_or_pipe: int | TextIO
        stderr_or_pipe: int | TextIO
        if use_venv:
            stdout_or_pipe, stderr_or_pipe = sys.stdout, sys.stderr
        else:
            stdout_or_pipe, stderr_or_pipe = PIPE, PIPE

        return Popen(
            arguments,
            stdout=stdout_or_pipe,
            stderr=stderr_or_pipe,
            cwd=cmd_context,
            **popen_kwargs,
        )

    def run_cmd(
        self,
        arguments: list[str],
        context: Optional[Path] = None,
        tee_to_stdout: bool = True,
        raise_on_failure: bool = False,
        # FIXME: tee output behaves weird with fish shell -> passing it
        # directly to stdout
        use_venv: bool = False,
        **popen_kwargs,
    ) -> CmdResult:
        process = self._prepare_process(arguments, context, use_venv, **popen_kwargs)
        stdout, stderr = "", ""
        if not use_venv:
            stdout = self._tee_process_output(process, tee_to_stdout, True).strip()
            stderr = self._tee_process_output(process, tee_to_stdout, False).strip()

        process.communicate()
        retval = process.poll()
        if retval is None:
            retval = FAILURE

        if raise_on_failure and retval != SUCCESS:
            raise PyVemException(
                f"Command `$ {' '.join(arguments)}` failed due to reason: {stderr}"
            )

        if use_venv:
            return CmdResult(retval=retval)

        logger.debug(
            f"Cmd results:\nstdout: {stdout};\nstderr: {stderr};\nretval: {retval}"
        )
        return CmdResult(stdout=stdout, stderr=stderr, retval=retval)
