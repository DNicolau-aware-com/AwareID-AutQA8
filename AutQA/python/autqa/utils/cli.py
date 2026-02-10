"""
CLI utilities and argument parsing helpers.

Common command-line argument handling for scripts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add common CLI arguments to parser.
    
    Adds standard arguments like --env-file, --verbose, --quiet, etc.
    
    Args:
        parser: ArgumentParser to add arguments to
        
    Example:
        parser = argparse.ArgumentParser()
        add_common_arguments(parser)
        args = parser.parse_args()
    """
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Path to .env file (default: python/.env)",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output (ERROR level only)",
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file",
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode",
    )


def add_enrollment_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add enrollment-specific arguments.
    
    Args:
        parser: ArgumentParser to add arguments to
    """
    parser.add_argument(
        "--username",
        type=str,
        help="Username for enrollment",
    )
    
    parser.add_argument(
        "--email",
        type=str,
        help="Email address",
    )
    
    parser.add_argument(
        "--enrollment-token",
        type=str,
        help="Enrollment token (overrides .env)",
    )
    
    parser.add_argument(
        "--workflow",
        type=str,
        default="charlie4",
        help="Workflow identifier (default: charlie4)",
    )


def add_authentication_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Add authentication-specific arguments.
    
    Args:
        parser: ArgumentParser to add arguments to
    """
    parser.add_argument(
        "--username",
        type=str,
        help="Username for authentication",
    )
    
    parser.add_argument(
        "--auth-token",
        type=str,
        help="Auth token (overrides .env)",
    )


def parse_log_level(args: argparse.Namespace) -> str:
    """
    Determine log level from CLI arguments.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR)
        
    Example:
        args = parser.parse_args()
        log_level = parse_log_level(args)
    """
    if args.verbose:
        return "DEBUG"
    elif args.quiet:
        return "ERROR"
    else:
        return "INFO"


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Prompt user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default answer if user just presses Enter
    
    Returns:
        True if user confirms, False otherwise
        
    Example:
        if confirm_action("Delete all data?"):
            delete_data()
    """
    prompt = f"{message} [{'Y/n' if default else 'y/N'}]: "
    
    while True:
        response = input(prompt).strip().lower()
        
        if not response:
            return default
        
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please answer 'y' or 'n'")


def print_separator(char: str = "=", length: int = 60) -> None:
    """
    Print a separator line.
    
    Args:
        char: Character to use for separator
        length: Length of separator
        
    Example:
        print_separator()
        print("TITLE")
        print_separator()
    """
    print(char * length)


def print_section(title: str, char: str = "=", length: int = 60) -> None:
    """
    Print a section header with separators.
    
    Args:
        title: Section title
        char: Character for separator
        length: Length of separator
        
    Example:
        print_section("Test Results")
    """
    print_separator(char, length)
    print(title)
    print_separator(char, length)