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

from pathlib import Path
import tempfile
import subprocess
import pysam

import logging
logger = logging.getLogger(__name__)

from breakpoint2bedsv import convert

def find_overlapping_breakpoints(breakpoint_bed, exclusion_file):
    """
    Find SVs whose breakpoints overlap exclusion regions.

    Parameters
    ----------
    breakpoint_bed : str or Path
        BED file containing SV breakpoints.
    exclusion_file : str or Path
        BED file containing exclusion regions.

    Returns
    -------
    set
        Set of SV IDs whose breakpoints overlap exclusion regions.

    Raises
    ------
    RuntimeError
        If bedtools is not installed or not available in PATH.
    RuntimeError
        If the bedtools intersect command fails.
    """

    logger.info("Finding breakpoints overlapping exclusion regions")

    # Find breakpoints overlapping exclusion regions
    ################################################
    try:
        result = subprocess.run(
            [
                "bedtools",
                "intersect",
                "-a", str(breakpoint_bed),
                "-b", str(exclusion_file),
                "-wa",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    # bedtools is not installed or not available in PATH
    except FileNotFoundError as exc:
        logger.error("bedtools is not installed or not available in PATH")
        raise RuntimeError(
            "bedtools is not installed or not available in PATH"
        ) from exc

    # bedtools is installed but the command failed
    except subprocess.CalledProcessError as exc:
        error_message = exc.stderr.strip() if exc.stderr else "unknown error"
        logger.error(f"bedtools intersect failed: {error_message}")
        raise RuntimeError(
            f"bedtools intersect failed: {error_message}"
        ) from exc


    # Extract SV IDs from the fourth BED column
    overlapping_ids = set()

    for line in result.stdout.splitlines():
        if line.strip():
            fields = line.split("\t")
            overlapping_ids.add(fields[3])

    logger.info(
        "Found %d SVs with overlapping breakpoints",
        len(overlapping_ids),
    )
    return overlapping_ids


def add_flag_in_vcf(input_file, output_file, overlapping_ids, flag):
    """
    Add an INFO flag to SVs in a VCF.

    Parameters
    ----------
    input_file : str or Path
        Input SV VCF, VCF.GZ or BCF file.
    output_file : str or Path
        Output annotated VCF file.
    overlapping_ids : set
        Set of SV IDs to flag.
    flag : str
        INFO flag to add to overlapping SVs.
    """

    # Open the input VCF
    ########################################################################
    with pysam.VariantFile(str(input_file)) as input_vcf:

        # Check that the requested INFO flag does not already exist
        # in the VCF header.
        ####################################################################
        if flag in input_vcf.header.info:
            raise ValueError(
                f"INFO flag already exists in VCF header: {flag}"
            )

        # Add the INFO flag to the VCF header.
        #
        # Number=0 and Type=Flag define a boolean INFO flag:
        # its presence indicates that the condition is true.
        ####################################################################
        input_vcf.header.info.add(
            flag,
            number=0,
            type="Flag",
            description=(
                "SV has at least one breakpoint overlapping an exclusion region"
            ),
        )

        # Open the output VCF using the modified header.
        ####################################################################
        with pysam.VariantFile(
            str(output_file),
            "w",
            header=input_vcf.header,
        ) as output_vcf:

            # Process each SV from the input VCF.
            ################################################################
            for record in input_vcf:

                # Add the flag if the SV ID is in the set of overlapping IDs.
                if record.id in overlapping_ids:
                    record.info[flag] = True

                # Write the record to the output VCF.
                output_vcf.write(record)
                

def annotate(input_file, exclusion_file, output_file, flag, tmp_dir=None):
    """
    Annotate SVs whose breakpoints overlap exclusion regions.

    Parameters
    ----------
    input_file : str or Path
        Input SV VCF, VCF.GZ or BCF file.
    exclusion_file : str or Path
        BED file containing exclusion regions.
    output_file : str or Path
        Output annotated VCF file.
    flag : str
        INFO flag to add to overlapping SVs.
    tmp_dir : str or Path, optional
        Directory where temporary files will be created.
        If None, the system default temporary directory is used.
    """

    # Create a temporary directory for intermediate files
    with tempfile.TemporaryDirectory(dir=tmp_dir) as tmpdir:

        # Convert SVs from the input VCF into breakpoint-level BED intervals
        ####################################################################
        logger.info("Starting breakpoint2bedsv conversion")
        breakpoint_bed = Path(tmpdir) / "breakpoints.bed"
        convert(
            input_file=input_file,
            output_file=breakpoint_bed,
        )


        # Identify breakpoints overlapping exclusion regions
        #####################################################
        logger.info("Starting breakpoint overlap analysis")
        overlapping_ids = find_overlapping_breakpoints(breakpoint_bed, exclusion_file)


        # Annotate the corresponding SVs in the output VCF
        ##################################################
        # Add the requested INFO flag to SVs whose breakpoints
        # overlap exclusion regions.
        logger.info("Starting annotating VCF with flag '%s'", flag)
        add_flag_in_vcf(
            input_file=input_file,
            output_file=output_file,
            overlapping_ids=overlapping_ids,
            flag=flag,
        )


    # Finished
    ##########
    logger.info("breakpoint2exclflagsv completed successfully")

    # Return the path to the annotated VCF
    #####################################
    return Path(output_file)