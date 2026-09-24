#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


FASTA_SEQUENCE_PATTERN = re.compile(r"^[ACGTRYSWKMBDHVN\-*]+$", re.IGNORECASE)
VALID_STRANDS = {"+", "-", ".", "?"}
VALID_PHASES = {"0", "1", "2", "."}


class ValidationError(Exception):
    pass


def validate_fasta(file_path: Path):
    identifiers = set()
    current_identifier = None
    current_has_sequence = False
    sequence_count = 0

    with file_path.open("r", encoding="utf-8") as fasta_file:
        for line_number, raw_line in enumerate(fasta_file, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_identifier is not None and not current_has_sequence:
                    raise ValidationError(
                        f"FASTA sequence '{current_identifier}' has no sequence data"
                    )
                identifier = line[1:].split(maxsplit=1)[0] if line[1:].strip() else ""
                if not identifier:
                    raise ValidationError(f"FASTA header on line {line_number} has no identifier")
                if identifier in identifiers:
                    raise ValidationError(f"Duplicate FASTA identifier: {identifier}")
                identifiers.add(identifier)
                current_identifier = identifier
                current_has_sequence = False
                sequence_count += 1
                continue

            if current_identifier is None:
                raise ValidationError(
                    f"FASTA sequence data appears before the first header on line {line_number}"
                )
            sequence = "".join(line.split())
            if not FASTA_SEQUENCE_PATTERN.fullmatch(sequence):
                raise ValidationError(
                    f"FASTA contains non-IUPAC DNA characters on line {line_number}"
                )
            current_has_sequence = True

    if sequence_count == 0:
        raise ValidationError("FASTA does not contain any sequences")
    if not current_has_sequence:
        raise ValidationError(f"FASTA sequence '{current_identifier}' has no sequence data")

    return {"sequenceCount": sequence_count}


def read_fai(fai_path: Path):
    sequences = {}
    with fai_path.open("r", encoding="utf-8") as fai_file:
        for line_number, line in enumerate(fai_file, start=1):
            columns = line.rstrip("\n").split("\t")
            if len(columns) < 2:
                raise ValidationError(f"Invalid FASTA index on line {line_number}")
            sequences[columns[0]] = int(columns[1])
    if not sequences:
        raise ValidationError("FASTA index does not contain any sequences")
    return sequences


def validate_gff3(file_path: Path, fai_path: Path):
    sequences = read_fai(fai_path)
    feature_count = 0
    version_seen = False

    with file_path.open("r", encoding="utf-8") as gff3_file:
        for line_number, raw_line in enumerate(gff3_file, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                continue
            if line.startswith("##gff-version"):
                version_seen = line.strip() == "##gff-version 3"
                if not version_seen:
                    raise ValidationError("GFF3 must declare '##gff-version 3'")
                continue
            if line.startswith("#"):
                continue

            columns = line.split("\t")
            if len(columns) != 9:
                raise ValidationError(f"GFF3 line {line_number} must contain 9 columns")
            seqid, _source, feature_type, start_value, end_value, _score, strand, phase, attributes = columns
            if seqid not in sequences:
                raise ValidationError(
                    f"GFF3 sequence ID '{seqid}' does not exist in the FASTA"
                )
            try:
                start = int(start_value)
                end = int(end_value)
            except ValueError as error:
                raise ValidationError(
                    f"GFF3 line {line_number} has non-integer coordinates"
                ) from error
            if start < 1 or end < start:
                raise ValidationError(f"GFF3 line {line_number} has invalid coordinates")
            if end > sequences[seqid]:
                raise ValidationError(
                    f"GFF3 line {line_number} ends beyond sequence '{seqid}'"
                )
            if not feature_type or feature_type == ".":
                raise ValidationError(f"GFF3 line {line_number} has no feature type")
            if strand not in VALID_STRANDS:
                raise ValidationError(f"GFF3 line {line_number} has an invalid strand")
            if phase not in VALID_PHASES:
                raise ValidationError(f"GFF3 line {line_number} has an invalid phase")
            if not attributes or attributes == ".":
                raise ValidationError(f"GFF3 line {line_number} has no attributes")
            feature_count += 1

    if not version_seen:
        raise ValidationError("GFF3 must start with the '##gff-version 3' directive")
    if feature_count == 0:
        raise ValidationError("GFF3 does not contain any features")
    return {"featureCount": feature_count, "sequenceCount": len(sequences)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=("FASTA", "GFF3"), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--fai", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.type == "FASTA":
            details = validate_fasta(args.input)
        else:
            if args.fai is None:
                raise ValidationError("GFF3 validation requires a FASTA index")
            details = validate_gff3(args.input, args.fai)
        report = {"valid": True, "type": args.type, "details": details}
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Validation completed successfully")
        return 0
    except (OSError, UnicodeError, ValidationError) as error:
        report = {"valid": False, "type": args.type, "error": str(error)}
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"VALIDATION_ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
