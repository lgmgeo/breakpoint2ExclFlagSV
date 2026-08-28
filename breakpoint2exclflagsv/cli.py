"""
breakpoint2exclflagsv/
Copyright (C) 2026-current Veronique Geoffroy (veronique.geoffroy@inserm.fr)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import logging
import platform

from breakpoint2exclflagsv.arguments import parse_args
from breakpoint2exclflagsv.logging_utils import setup_logging
from breakpoint2exclflagsv.core import annotate
from breakpoint2exclflagsv import __version__

import subprocess
import breakpoint2bedsv
import variant_extractor
from importlib.metadata import version


# Module-level logger.
# The logging configuration is initialized in main() after parsing
# the command-line arguments.
logger = logging.getLogger(__name__)

def get_bedtools_version():
    """
    Return the installed bedtools version.
    """

    try:
        result = subprocess.run(
            ["bedtools", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    except (FileNotFoundError, subprocess.CalledProcessError):
        return "not installed"

def log_cli_info(args):

    # Display
    #########
    logger.info("breakpoint2exclflagsv %s", __version__)
    logger.info("Copyright (C) 2026-current GEOFFROY Veronique")
    logger.info(
        "Please feel free to create a Github issue for any suggestions "
        "or bug reports"
    )
    logger.info("https://github.com/lgmgeo/breakpoint2exclflagsv/issues")
    logger.info("Python version: %s", platform.python_version())

    logger.debug("breakpoint2bedsv version: %s", breakpoint2bedsv.__version__)
    logger.debug("variant_extractor version: %s", variant_extractor.__version__)
    logger.debug("bedtools version: %s", get_bedtools_version())
    logger.debug("importlib.metadata version: %s", version("importlib-metadata"))
    logger.debug("platform: %s", platform.platform())
    logger.debug("sys.executable: %s", sys.executable)
    logger.debug("sys.argv: %s", sys.argv)    

    # Arguments display
    ###################
    logger.info("Listing arguments")
    logger.info("           ***************************************************")
    logger.info("           breakpoint2exclflagsv has been run with these arguments:")
    logger.info("           ***************************************************")

    for key, value in sorted(vars(args).items()):
        if value in ("", None):
            continue

        key = key.replace("_", "-")
        logger.info("           --%s %s", key, value)

    logger.info("           ***************************************************")


def main(argv=None):
    """
    Main entry point for the breakpoint2exclflagsv command-line interface.

    Parameters
    ----------
    argv : list[str] or None
        Command-line arguments.
        If None, arguments are read from sys.argv.

    Returns
    -------
    int
        Exit status:
        - 0: successful execution
        - 1: unexpected error
        - 2: input or argument validation error
    """

    # Use the arguments provided by the caller.
    # When called from the command line, use sys.argv instead.
    if argv is None:
        argv = sys.argv[1:]

    try:
        # Parse and validate command-line arguments.
        # This also sets default values for optional arguments.
        args = parse_args(argv)

        # Configure the logging system according to the command-line
        # options (--verbose and --log-file).
        setup_logging(
            verbose=args.verbose,
            log_file=args.log_file,
        )

        # Display CLI arguments and runtime information.
        log_cli_info(args)

        # Execute the main breakpoint exclusion annotation pipeline.
        # Errors are allowed to propagate and are handled below.
        output_file = annotate(
            input_file=args.input_file,
            exclusion_file=args.exclusion_file,
            output_file=args.output_file,
            flag=args.flag,
            tmp_dir=args.tmp_dir,
        )

        logger.info("Annotated VCF created: %s", output_file)

    except ValueError as e:
        # Input or configuration error.
        # Return a dedicated exit code so that the caller can
        # distinguish validation errors from unexpected failures.
        logger.error("%s", e)
        return 2

    except Exception:
        # Catch any unexpected error.
        # logger.exception() automatically includes the traceback,
        # which is useful for debugging.
        logger.exception("Unexpected error")
        return 1

    # The pipeline completed successfully.
    return 0


if __name__ == "__main__":
    sys.exit(main())
