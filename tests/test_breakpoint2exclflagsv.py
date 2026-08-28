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
from breakpoint2exclflagsv import annotate
from breakpoint2exclflagsv.core import find_overlapping_breakpoints
import subprocess
import pytest
import pysam

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tests" / "data"

# pytest fixture provides an automatically prepared test resource:
# - a unique temporary directory for test output: tmp_path


# def test_breakpoint2bedsv_api(tmp_path):
#     input_vcf = (
#         BASE
#         / "test_01_angle-bracketed_notation"
#         / "input"
#         / "test.vcf"
#     )

#     expected_bed = (
#         BASE
#         / "test_01_angle-bracketed_notation"
#         / "expected"
#         / "test.bed"
#     )

#     exclusion_file = (
#         BASE
#         / "test_01_angle-bracketed_notation"
#         / "input"
#         / "excluded-regions.bed"
#     )

#     result = annotate(
#         input_file=input_vcf,
#         exclusion_file=exclusion_file,
#         output_file="dummy.vcf",
#         flag="gnomAD_excl",
#     )

#     assert result == expected_bed.read_text()


def test_find_overlapping_breakpoints(tmp_path):

    breakpoint_bed = tmp_path / "breakpoints.bed"
    exclusion_bed = tmp_path / "exclusion.bed"

    breakpoint_bed.write_text(
        "chr1\t100\t101\tSV1\n"
        "chr1\t200\t201\tSV2\n"
        "chr2\t300\t301\tSV3\n"
    )

    exclusion_bed.write_text(
        "chr1\t50\t150\n"
        "chr2\t250\t350\n"
    )

    result = find_overlapping_breakpoints(
        breakpoint_bed=breakpoint_bed,
        exclusion_file=exclusion_bed,
    )

    assert result == {"SV1", "SV3"}


def test_find_overlapping_breakpoints_bedtools_error(tmp_path, monkeypatch):
    breakpoint_bed = tmp_path / "breakpoints.bed"
    exclusion_bed = tmp_path / "exclusion.bed"

    breakpoint_bed.write_text(
        "chr1\t100\t101\tSV1\n"
    )

    exclusion_bed.write_text(
        "chr1\t50\t150\n"
    )

    # Mock subprocess.run() to simulate a failure of bedtools. 
    # This avoids having to actually run bedtools with an invalid input.
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=args[0],
            stderr="Error: invalid BED file",
        )

    # Temporarily replace subprocess.run() with the mock function. 
    # During this test, calling subprocess.run() will therefore raise 
    # the simulated CalledProcessError instead of executing bedtools.
    monkeypatch.setattr("subprocess.run", mock_run)

    # Check that the CalledProcessError raised by bedtools is caught 
    # and converted into a RuntimeError with a clear error message.
    with pytest.raises(
        RuntimeError,
        match="bedtools intersect failed: Error: invalid BED file",
    ):
        find_overlapping_breakpoints(
            breakpoint_bed=breakpoint_bed,
            exclusion_file=exclusion_bed,
        )


def test_annotate(tmp_path):
    input_vcf = (
        BASE
        / "test_01_angle-bracketed_notation"
        / "input"
        / "test.vcf"
    )

    exclusion_file = (
        BASE
        / "test_01_angle-bracketed_notation"
        / "input"
        / "excluded-regions.bed"
    )

    output_vcf = tmp_path / "output.vcf"

    result = annotate(
        input_file=input_vcf,
        exclusion_file=exclusion_file,
        output_file=output_vcf,
        flag="gnomAD_excl",
    )

    # Check that annotate() returns the output path.
    assert result == output_vcf

    # Check that the output VCF was created.
    assert output_vcf.exists()

    # Read the annotated VCF.
    with pysam.VariantFile(output_vcf) as vcf:

        # Check that the requested INFO flag was added to the header.
        assert "gnomAD_excl" in vcf.header.info

        records = list(vcf)

    # Check that the expected number of variants is unchanged.
    assert len(records) == 1

    # Check that the expected SV was flagged.
    assert "gnomAD_excl" in records[0].info