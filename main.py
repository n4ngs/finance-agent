#!/usr/bin/env python3
"""
Personal CFO - Main Entry Point
"""

import sys
import os
from cli import CFOCLI


def main():
    """Start the Personal CFO application."""
    
    # Set up database path
    db_path = os.path.expanduser("~/.personal-cfo/finance.db")
    db_dir = os.path.dirname(db_path)
    
    # Create directory if needed
    os.makedirs(db_dir, exist_ok=True)
    
    # Run CLI
    cli = CFOCLI(db_path)
    cli.run()
    cli.cfo.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)
