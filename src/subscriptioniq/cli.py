"""Command-line operations for reproducible demos."""
import argparse
from .generate import write_data
from .warehouse import build_warehouse


def main():
    parser = argparse.ArgumentParser(prog="subscriptioniq")
    sub = parser.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("generate", help="Generate fictional CSV data")
    seed.add_argument("--out", default="data")
    seed.add_argument("--customers", type=int, default=420)
    seed.add_argument("--seed", type=int, default=42)
    build = sub.add_parser("build", help="Build SQLite marts and CSV reports")
    build.add_argument("--data", default="data")
    build.add_argument("--db", default="warehouse/subscriptioniq.db")
    build.add_argument("--reports", default="reports")
    args = parser.parse_args()
    if args.command == "generate":
        write_data(args.out, seed=args.seed, customers=args.customers)
    else:
        build_warehouse(args.data, args.db, args.reports)


if __name__ == "__main__":
    main()
