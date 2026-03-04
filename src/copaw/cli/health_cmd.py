# -*- coding: utf-8 -*-
"""CLI health command: alias for doctor check."""
import click

from .doctor_cmd import check_cmd


@click.command("health")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results in JSON format.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information.",
)
@click.pass_context
def health_cmd(ctx: click.Context, output_json: bool, verbose: bool) -> None:
    """Run system health check (alias for 'doctor check').

    This is a shorthand for 'copaw doctor check'.
    """
    ctx.invoke(check_cmd, output_json=output_json, verbose=verbose)


@click.command("check")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results in JSON format.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information.",
)
@click.pass_context
def check_alias_cmd(ctx: click.Context, output_json: bool, verbose: bool) -> None:
    """Run system health check (alias for 'doctor check').

    This is a shorthand for 'copaw doctor check'.
    """
    ctx.invoke(check_cmd, output_json=output_json, verbose=verbose)
