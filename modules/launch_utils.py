import importlib.metadata
import os
import re
import subprocess

from packaging import version

re_requirement = re.compile(r"\s*([-_a-zA-Z0-9]+)\s*(?:==\s*([-+_.a-zA-Z0-9]+))?\s*")


def requirements_met(requirements_file: str) -> bool:
    """
    Parses a requirements.txt file to determine if all requirements in it
    are already installed.

    Args:
        requirements_file (str): The path to the requirements.txt file.

    Returns:
        bool: True if all requirements are installed, False otherwise.
    """

    with open(requirements_file, "r", encoding="utf8") as file:
        for line in file:
            if line.strip() == "":
                continue

            m = re.match(re_requirement, line)
            if m is None:
                return False

            package = m.group(1).strip()
            version_required = (m.group(2) or "").strip()

            try:
                version_installed = importlib.metadata.version(package)
            except ImportError:
                return False
            if version_required == "":
                continue
            if version.parse(version_required) != version.parse(version_installed):
                return False

    return True


# Whether to default to printing command output


def run(command: str, desc: str = None, err_desc: str = None, custom_env: dict = None, live: bool = True) -> str:
    """
    Run a command and return the output.

    Args:
        command (str): The command to run.
        desc (str, optional): Description of the command. Defaults to None.
        err_desc (str, optional): Description of the error. Defaults to None.
        custom_env (dict, optional): Custom environment variables. Defaults to None.
        live (bool, optional): Whether to print the command output. Defaults to True.

    Returns:
        str: The command output.

    Raises:
        RuntimeError: If the command returns a non-zero exit code.
    """
    if desc is not None:
        print(desc)

    run_kwargs = {
        "args": command,
        "shell": True,
        "env": os.environ if custom_env is None else custom_env,
        "encoding": "utf8",
        "errors": "ignore",
    }

    if not live:
        run_kwargs["stdout"] = run_kwargs["stderr"] = subprocess.PIPE

    result = subprocess.run(**run_kwargs)

    if result.returncode != 0:
        error_bits = [
            f"{err_desc or 'Error running command'}.",
            f"Command: {command}",
            f"Error code: {result.returncode}",
        ]
        if result.stdout:
            error_bits.append(f"stdout: {result.stdout}")
        if result.stderr:
            error_bits.append(f"stderr: {result.stderr}")
        raise RuntimeError("\n".join(error_bits))

    return result.stdout or ""


def run_pip_install(command: str, desc: str, live: bool = True) -> str:
    """

    Args:
        command ():
        desc ():
        live ():

    Returns:

    """
    return run(
        f"python -m pip {command} --prefer-binary",
        desc=f"Installing {desc}",
        err_desc=f"Couldn't install {desc}",
        live=live,
    )


def install_requirements(
    requirement_file_path: str,
):
    """
    Install the requirements specified in the given requirement file.

    Args:
        requirement_file_path (str): The path to the requirement file.

    Returns:
        None

    """
    dirname = os.path.dirname(requirement_file_path)
    if requirements_met(requirement_file_path):
        print(f"requirements for {dirname} is already satisfied")
        return
    print(
        run_pip_install(
            command=f"install -r {requirement_file_path}",
            desc=f"requirements for {dirname}",
        )
    )
