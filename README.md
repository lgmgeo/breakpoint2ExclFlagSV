
<div align="center">
  <h1 style="font-weight: bold; margin-bottom: 0.2em;">breakpoint2ExclFlagSV</h1>
  <h3 style="margin-top: 0;">Flags/Annotates SVs based on breakpoint overlap with exclusion regions
</h3>
</div>

The tool is designed to identify SVs for which at least one breakpoint overlaps a set of genomic exclusion regions and to annotate these SVs in the input VCF/BCF.

The tool does not remove SVs from the VCF/BCF input file. It adds an INFO flag to the corresponding records.

- [Workflow](#workflow)
- [Example application: Cohort assessment of SV presence/absence using gnomAD SVs as reference](#example-application-cohort-assessment-of-sv-presenceabsence-using-gnomad-svs-as-reference)
  - [Context](#context)
  - [Annotation to evaluate the SV presence/absence using gnomAD SVs as reference](#annotation-to-evaluate-the-sv-presenceabsence-using-gnomad-svs-as-reference)
  - [gnomAD exclusion resources](#gnomad-exclusion-resources)
    - [gnomAD SVs v4.1 exclusion regions (GRCh38)](#gnomad-svs-v41-exclusion-regions-grch38)
    - [gnomad SVs v2.0 exclusion regions (GRCh37)](#gnomad-svs-v20-exclusion-regions-grch37)
- [Quick Installation](#quick-installation)
  - [Install from PyPI](#install-from-pypi)
  - [Upgrade](#upgrade)
  - [Install from GitHub](#install-from-github)
- [Python API](#python-api)
- [Run the test suite](#run-the-test-suite)
- [Command-line interface](#command-line-interface)
  - [Usage](#usage)
- [Output annotation](#output-annotation)
- [Dependencies](#dependencies)
- [How to cite?](#how-to-cite)
- [License](#license)

## Workflow

```text
SVs (VCF/VCF.GZ/BCF)
  │
  ├── breakpoint2BedSV
  │      → convert SVs into breakpoint-level BED intervals
  │
  ├── bedtools intersect
  │      → identify breakpoints overlapping exclusion regions
  │
  ├── collect SV IDs
  │
  └── annotate VCF
         → add INFO flag (user defined)
```

The exclusion regions can be provided as a BED file. 

## Example application: Cohort assessment of SV presence/absence using gnomAD SVs as reference

### Context

In their protocol, gnomAD excluded any variants whose breakpoints mapped within their PE/SR clustering blacklists.

Indeed, SV calling is less reliable in some genomic regions due to:

- low mappability / depth bias
- peri-centromeric or peri-telomeric repeats
- known problematic regions in population datasets such as gnomAD
  
### Annotation to evaluate the SV presence/absence using gnomAD SVs as reference

=> Annotation of PE/SR-based SVs in a VCF with a `gnomAD_excl` flag when at least one breakpoint overlaps a gnomAD SV exclusion region.
(<i>cf</i> <a href="https://discuss.gnomad.broadinstitute.org/t/centromeric-del-detected-by-manta-and-visible-in-coverage-but-missing-from-gnomad-sv/833" target="_blank">discussion</a> in the gnomAD forum)

<img src="./doc/excluded_regions_overlap.png" alt="SV schema"/>

### gnomAD exclusion resources

#### gnomAD SVs v4.1 exclusion regions (GRCh38)

```bash
curl -O https://storage.googleapis.com/gatk-sv-resources-public/hg38/v0/sv-resources/resources/v1/depth_blacklist.sorted.bed.gz
curl -O  https://storage.googleapis.com/gatk-sv-resources-public/hg38/v0/sv-resources/resources/v1/PESR.encode.peri_all.repeats.delly.hg38.blacklist.sorted.bed.gz
```

#### gnomad SVs v2.0 exclusion regions (GRCh37)

```bash
curl -O https://github.com/hall-lab/speedseq/blob/master/annotations/ceph18.b37.lumpy.exclude.2014-01-15.bed
```

## Quick Installation

### Install from PyPI

The recommended way to install `breakpoint2exclflagsv/` is with `pip`:

```bash
pip install breakpoint2exclflagsv/
```

Then verify the installation:

```bash
breakpoint2exclflagsv/ --help
```

### Upgrade

To upgrade to the latest version:

```bash
pip install --upgrade breakpoint2exclflagsv/
```

### Install from GitHub

To install the latest development version directly from GitHub:

```bash
git clone https://github.com/lgmgeo/breakpoint2exclflagsv/.git
cd breakpoint2exclflagsv/
poetry install
```

Then run:

```bash
poetry run breakpoint2exclflagsv/ --help
```

## Python API

breakpoint2ExclFlagSV is designed to provide a Python API that can be used independently of its command-line interface.

The main public function is:

```python
from breakpoint2ExclFlagSV import annotate

annotate(
    input_file="input.vcf.gz",
    exclusion_file="exclusion_regions.bed.gz",
    output_file="annotated.vcf.gz",
    flag="flag_excl",
)
```
The annotate() function will:

- convert SVs into breakpoint-level BED intervals using breakpoint2exclflagsv/;
- identify breakpoints overlapping exclusion regions;
- collect the corresponding SV IDs;
- add the specified INFO flag to the corresponding SVs in the output VCF.

## Run the test suite

To run all tests locally:

```bash
poetry run pytest -v
```

To list the collected tests without executing them:

```bash
poetry run pytest --collect-only
```

The test data and test scripts are located in the `tests/` directory.

All tests are also executed automatically through GitHub Actions on each push and pull request.


## Command-line interface

### Usage

```
usage: breakpoint2exclflagsv [-h] [-V] [--log-file <File>] -i <File> -e <File> [-d <Dir>] -o <File> -f <Flag> [-T <Dir>] [-v]

Flags SVs based on breakpoint overlap with exclusion regions.

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  --log-file <File>     write log messages to the specified file

Input files:
  -i <File>, --input-file <File>
                        the SV VCF/BCF input file
                        VCF/VCF.gz/BCF files are supported
                        multi-allelic lines are not allowed
                        required
  -e <File>, --exclusion-file <File>
                        BED file containing exclusion regions required

Output options:
  -d <Dir>, --output-dir <Dir>
                        the output directory
                        default: current directory
  -o <File>, --output-file <File>
                        output annotated VCF file
                        required

Annotation:
  -f <Flag>, --flag <Flag>
                        INFO flag to add to SVs whose breakpoints
                                overlap exclusion regions
                                required

Behavior:
  -T <Dir>, --tmp-dir <Dir>
                        directory where temporary files will be created
                        if not provided, the system default temporary directory is used
  -v, --verbose         enable verbose output
```

## Output annotation

An SV is annotated with the user-defined INFO flag when at least one of its breakpoints overlaps an exclusion region.

For example, with `flag="gnomAD_excl"`:

```text
##INFO=<ID=gnomAD_excl,Number=0,Type=Flag,Description="SV breakpoint overlaps an exclusion region">
```

The SV remains in the output VCF; only the annotation is added.

## Dependencies

The main dependencies are:

- breakpoint2exclflagsv/ for SV breakpoint extraction;
- pysam for VCF/BCF processing;
- bedtools for genomic interval intersection.

## How to cite?

Please cite the following doi if you are using this tool in your research:<br>
[![DOI](./doc/zenodo.21134592.svg)](https://doi.org/10.5281/zenodo.21134592)

## License

breakpoint2bedsv is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

breakpoint2bedsv is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

See the `LICENSE` file for the full license text.
