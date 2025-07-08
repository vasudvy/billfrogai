"""
Billfrog - A CLI tool for generating and emailing AI usage receipts.
"""

__version__ = "0.1.0"
__author__ = "Billfrog Contributors"
__email__ = "hello@billfrog.dev"

# CLI main function is imported on demand to avoid dependency issues
def main():
    """Main entry point for CLI."""
    from .cli import main as cli_main
    return cli_main()

__all__ = ["main"]