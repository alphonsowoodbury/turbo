"""Shell completion command."""

import os
from pathlib import Path

import click
from rich.console import Console

from turbo.cli.utils import handle_exceptions

console = Console()


@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
@click.option("--install", is_flag=True, help="Install completion for the current user")
@handle_exceptions
def completion_command(shell, install):
    """Generate shell completion scripts."""
    if install:
        _install_completion(shell)
    else:
        _generate_completion(shell)


def _generate_completion(shell):
    """Generate completion script for the specified shell."""
    if shell == "bash":
        completion_script = _get_bash_completion()
    elif shell == "zsh":
        completion_script = _get_zsh_completion()
    elif shell == "fish":
        completion_script = _get_fish_completion()
    else:
        console.print(f"[red]Unsupported shell: {shell}[/red]")
        return

    console.print(completion_script)


def _install_completion(shell):
    """Install completion script for the current user."""
    try:
        if shell == "bash":
            _install_bash_completion()
        elif shell == "zsh":
            _install_zsh_completion()
        elif shell == "fish":
            _install_fish_completion()
        else:
            console.print(f"[red]Unsupported shell: {shell}[/red]")
            return

        console.print(f"[green]✓[/green] Shell completion installed for {shell}")
        console.print(
            "[yellow]Note: You may need to restart your shell or source your profile[/yellow]"
        )

    except Exception as e:
        console.print(f"[red]Failed to install completion: {e}[/red]")


def _get_bash_completion():
    """Generate bash completion script."""
    return """# Turbo CLI completion for bash
_turbo_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _TURBO_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

complete -o nosort -F _turbo_completion turbo
"""


def _get_zsh_completion():
    """Generate zsh completion script."""
    return """#compdef turbo

_turbo_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[turbo] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _TURBO_COMPLETE=zsh_complete turbo)}")

    for type_and_line in $response; do
        completions+=(${type_and_line#*,})
    done

    if [ "$completions" ]; then
        _describe 'completions' completions
    fi
}

_turbo_completion "$@"
"""


def _get_fish_completion():
    """Generate fish completion script."""
    return """# Turbo CLI completion for fish
function __turbo_complete
    set -lx COMP_WORDS (commandline -o)
    set -lx COMP_CWORD (math (count $COMP_WORDS) - 1)
    turbo | string split0
end

complete -f -c turbo -a "(__turbo_complete)"
"""


def _install_bash_completion():
    """Install bash completion."""
    completion_script = _get_bash_completion()

    # Try different bash completion directories
    completion_dirs = [
        Path.home() / ".bash_completion.d",
        Path("/usr/local/etc/bash_completion.d"),
        Path("/etc/bash_completion.d"),
    ]

    installed = False
    for comp_dir in completion_dirs:
        if comp_dir.exists() and os.access(comp_dir, os.W_OK):
            completion_file = comp_dir / "turbo"
            with open(completion_file, "w") as f:
                f.write(completion_script)
            installed = True
            break

    if not installed:
        # Fall back to adding to .bashrc
        bashrc = Path.home() / ".bashrc"
        with open(bashrc, "a") as f:
            f.write("\n# Turbo CLI completion\n")
            f.write(completion_script)


def _install_zsh_completion():
    """Install zsh completion."""
    completion_script = _get_zsh_completion()

    # Create zsh completion directory if it doesn't exist
    comp_dir = Path.home() / ".zsh" / "completions"
    comp_dir.mkdir(parents=True, exist_ok=True)

    completion_file = comp_dir / "_turbo"
    with open(completion_file, "w") as f:
        f.write(completion_script)

    # Add to fpath in .zshrc if not already there
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        with open(zshrc) as f:
            content = f.read()

        if "fpath=(~/.zsh/completions $fpath)" not in content:
            with open(zshrc, "a") as f:
                f.write("\n# Turbo CLI completion\n")
                f.write("fpath=(~/.zsh/completions $fpath)\n")
                f.write("autoload -U compinit && compinit\n")


def _install_fish_completion():
    """Install fish completion."""
    completion_script = _get_fish_completion()

    # Fish completion directory
    comp_dir = Path.home() / ".config" / "fish" / "completions"
    comp_dir.mkdir(parents=True, exist_ok=True)

    completion_file = comp_dir / "turbo.fish"
    with open(completion_file, "w") as f:
        f.write(completion_script)
