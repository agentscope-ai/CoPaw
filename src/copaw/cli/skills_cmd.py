from __future__ import annotations

import click
from typing import Optional, List

from ..agents.skills_manager import SkillService, list_available_skills
from ..config.utils import load_config, save_config
from ..config.config import SkillsConfig
from .utils import prompt_checkbox, prompt_confirm, prompt_choice


# pylint: disable=too-many-branches
def configure_skills_interactive() -> None:
    """Interactively select which skills to enable (multi-select)."""
    all_skills = SkillService.list_all_skills()
    if not all_skills:
        click.echo("No skills found. Nothing to configure.")
        return

    available = set(list_available_skills())
    all_names = {s.name for s in all_skills}

    # Default to all skills if nothing is currently active (first time)
    default_checked = available if available else all_names

    # Build checkbox options: (label, value)
    options: list[tuple[str, str]] = []
    for skill in sorted(all_skills, key=lambda s: s.name):
        status = "✓" if skill.name in available else "✗"
        label = f"{skill.name}  [{status}] ({skill.source})"
        options.append((label, skill.name))

    click.echo("\n=== Skills Configuration ===")
    click.echo("Use ↑/↓ to move, <space> to toggle, <enter> to confirm.\n")

    selected = prompt_checkbox(
        "Select skills to enable:",
        options=options,
        checked=default_checked,
        select_all_option=False,
    )

    # Ctrl+C → cancel
    if selected is None:
        click.echo("\n\nOperation cancelled.")
        return

    selected_set = set(selected)

    # Show preview of changes
    to_enable = selected_set - available
    to_disable = (all_names & available) - selected_set

    if not to_enable and not to_disable:
        click.echo("\nNo changes needed.")
        return

    click.echo()
    if to_enable:
        click.echo(
            click.style(
                f"  + Enable:  {', '.join(sorted(to_enable))}",
                fg="green",
            ),
        )
    if to_disable:
        click.echo(
            click.style(
                f"  - Disable: {', '.join(sorted(to_disable))}",
                fg="red",
            ),
        )

    # Confirm save or skip
    save = prompt_confirm("Apply changes?", default=True)
    if not save:
        click.echo("Skipped. No changes applied.")
        return

    # Apply changes
    for name in to_enable:
        result = SkillService.enable_skill(name)
        if result:
            click.echo(f"  ✓ Enabled: {name}")
        else:
            click.echo(
                click.style(f"  ✗ Failed to enable: {name}", fg="red"),
            )

    for name in to_disable:
        result = SkillService.disable_skill(name)
        if result:
            click.echo(f"  ✓ Disabled: {name}")
        else:
            click.echo(
                click.style(f"  ✗ Failed to disable: {name}", fg="red"),
            )

    click.echo("\n✓ Skills configuration updated!")


def configure_skills_registration() -> None:
    """Configure skills registration filtering (which skills the agent loads at startup)."""
    # Load current config
    config = load_config()
    skills_config = getattr(config, 'skills', SkillsConfig())
    
    click.echo("\n=== Skills Registration Configuration ===")
    click.echo("Configure which skills are loaded when the agent starts.\n")
    
    # Current status
    current_enabled = skills_config.enabled or []
    current_strict = skills_config.strict_mode
    
    click.echo(f"Current configuration:")
    click.echo(f"  Enabled skills: {current_enabled if current_enabled else 'All skills'}")
    click.echo(f"  Strict mode: {current_strict}\n")
    
    # Choose action
    action = prompt_choice(
        "What would you like to do?",
        [
            ("Keep current configuration", "keep"),
            ("Enable specific skills only", "specific"),
            ("Enable all skills", "all"),
            ("Toggle strict mode", "strict"),
        ],
    )
    
    if action == "keep":
        click.echo("Configuration unchanged.")
        return
    
    new_enabled: Optional[List[str]] = None
    new_strict: bool = current_strict
    
    if action == "specific":
        # Get all available skills
        all_skills = SkillService.list_all_skills()
        if not all_skills:
            click.echo("No skills found.")
            return
            
        skill_names = [s.name for s in all_skills]
        current_selection = set(current_enabled) if current_enabled else set(skill_names)
        
        options = [(name, name) for name in sorted(skill_names)]
        
        selected = prompt_checkbox(
            "Select skills to register at startup:",
            options=options,
            checked=current_selection,
            select_all_option=True,
        )
        
        if selected is None:
            click.echo("Cancelled.")
            return
            
        new_enabled = list(selected) if selected else None
        
    elif action == "all":
        new_enabled = None  # None means "all skills"
        
    elif action == "strict":
        new_strict = not current_strict
        new_enabled = current_enabled  # Keep current enabled list
        
    # Preview changes
    click.echo(f"\nNew configuration:")
    click.echo(f"  Enabled skills: {new_enabled if new_enabled else 'All skills'}")
    click.echo(f"  Strict mode: {new_strict}")
    
    if prompt_confirm("\nApply changes?", default=True):
        # Update config
        config.skills = SkillsConfig(enabled=new_enabled, strict_mode=new_strict)
        save_config(config)
        click.echo("✓ Skills registration configuration updated!")
        
        # Show impact
        if new_enabled is not None and new_strict:
            click.echo(f"Agent will load only these {len(new_enabled)} skills at startup.")
        elif new_enabled is not None:
            click.echo(f"Agent will prioritize these {len(new_enabled)} skills.")
        else:
            click.echo("Agent will load all available skills at startup.")
    else:
        click.echo("Cancelled. No changes made.")


@click.group("skills")
def skills_group() -> None:
    """Manage skills (list / configure)."""


@skills_group.command("list")
def list_cmd() -> None:
    """Show all skills and their enabled/disabled status."""
    all_skills = SkillService.list_all_skills()
    available = set(list_available_skills())

    if not all_skills:
        click.echo("No skills found.")
        return

    click.echo(f"\n{'─' * 50}")
    click.echo(f"  {'Skill Name':<30s} {'Source':<12s} Status")
    click.echo(f"{'─' * 50}")

    for skill in sorted(all_skills, key=lambda s: s.name):
        status = (
            click.style("✓ enabled", fg="green")
            if skill.name in available
            else click.style("✗ disabled", fg="red")
        )
        click.echo(f"  {skill.name:<30s} {skill.source:<12s} {status}")

    click.echo(f"{'─' * 50}")
    enabled_count = sum(1 for s in all_skills if s.name in available)
    click.echo(
        f"  Total: {len(all_skills)} skills, "
        f"{enabled_count} enabled, "
        f"{len(all_skills) - enabled_count} disabled\n",
    )


@skills_group.command("config")
def configure_cmd() -> None:
    configure_skills_interactive()


@skills_group.command("registration")
def registration_cmd() -> None:
    """Configure which skills are loaded at agent startup."""
    configure_skills_registration()
