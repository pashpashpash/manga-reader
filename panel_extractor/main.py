# stdlib
import argparse
from argparse import RawTextHelpFormatter

# project
from panel_extractor import PanelExtractor


def main(args):
    panel_extractor = PanelExtractor(
        keep_text=args.keep_text,
        min_pct_panel=args.min_panel,
        max_pct_panel=args.max_panel,
    )
    panel_extractor.extract(args.folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Implementation of a Manga Panel Extractor and dialogue bubble text eraser.",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        "-kt",
        "--keep_text",
        action="store_true",
        help="Do not erase the dialogue bubble text.",
    )
    parser.add_argument(
        "-minp",
        "--min_panel",
        type=int,
        choices=range(1, 99),
        default=2,
        metavar="[1-99]",
        help="Percentage of minimum panel area in relation to total page area.",
    )
    parser.add_argument(
        "-maxp",
        "--max_panel",
        type=int,
        choices=range(1, 99),
        default=90,
        metavar="[1-99]",
        help="Percentage of minimum panel area in relation to total page area.",
    )
    parser.add_argument(
        "-f",
        "--folder",
        default="./images/",
        type=str,
        help="""folder path to input manga pages.
Panels will be saved to a directory named `panels` in this folder.""",
    )

    args = parser.parse_args()
    main(args)
