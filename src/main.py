"""
CLI entry point for the Autonomous GitHub Code-Quality Auditor.
"""

import argparse
import sys
from dotenv import load_dotenv

from src.controller import AuditController


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous GitHub Repository Code-Quality Auditor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository URL to audit (e.g. https://github.com/psf/requests)",
    )
    parser.add_argument(
        "--focus",
        default="all",
        help="Specific audit focus areas: security, maintainability, testing, performance, reliability, or all",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LiteLLM model string (defaults to 'gemini/gemini-2.0-flash', supports 'gpt-4o', etc.)",
    )
    parser.add_argument(
        "--output",
        default="outputs/report",
        help="Output filepath prefix for .md and .json reports",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional GitHub Personal Access Token (or set GITHUB_TOKEN in .env)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    load_dotenv()
    args = parse_args()

    controller = AuditController(
        repo_url=args.repo,
        focus=args.focus,
        model=args.model,
        output_prefix=args.output,
        github_token=args.token,
        verbose=args.verbose,
    )

    report = controller.run()
    if report is None:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()