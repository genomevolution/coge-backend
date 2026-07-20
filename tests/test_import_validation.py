from pathlib import Path

import pytest

from workflows.scripts.validate_import import (
  ValidationError,
  validate_fasta,
  validate_gff3
)


def write_file(tmp_path: Path, name: str, content: str) -> Path:
  file_path = tmp_path / name
  file_path.write_text(content, encoding="utf-8")
  return file_path


def test_valid_fasta(tmp_path):
  fasta = write_file(tmp_path, "genome.fa", ">chr1\nACGTRYSWKMBDHVN\n>chr2 description\nNNNN\n")

  result = validate_fasta(fasta)

  assert result == {"sequenceCount": 2}


@pytest.mark.parametrize(
  "content, expected_error",
  [
    ("", "does not contain any sequences"),
    (">chr1\nACGT\n>chr1\nTT\n", "Duplicate FASTA identifier"),
    (">chr1\nACGTZ\n", "non-IUPAC DNA characters"),
    (">chr1\n", "has no sequence data")
  ]
)
def test_invalid_fasta(tmp_path, content, expected_error):
  fasta = write_file(tmp_path, "invalid.fa", content)

  with pytest.raises(ValidationError, match=expected_error):
    validate_fasta(fasta)


def test_valid_compatible_gff3(tmp_path):
  fai = write_file(tmp_path, "genome.fa.fai", "chr1\t100\t0\t100\t101\n")
  gff3 = write_file(
    tmp_path,
    "annotation.gff3",
    "##gff-version 3\nchr1\tsource\tgene\t1\t50\t.\t+\t.\tID=gene1\n"
  )

  result = validate_gff3(gff3, fai)

  assert result == {"featureCount": 1, "sequenceCount": 1}


@pytest.mark.parametrize(
  "feature, expected_error",
  [
    ("chr2\tsource\tgene\t1\t50\t.\t+\t.\tID=gene1", "does not exist"),
    ("chr1\tsource\tgene\t1\t101\t.\t+\t.\tID=gene1", "ends beyond"),
    ("chr1 source gene 1 50 . + . ID=gene1", "9 columns")
  ]
)
def test_invalid_or_incompatible_gff3(tmp_path, feature, expected_error):
  fai = write_file(tmp_path, "genome.fa.fai", "chr1\t100\t0\t100\t101\n")
  gff3 = write_file(
    tmp_path,
    "annotation.gff3",
    f"##gff-version 3\n{feature}\n"
  )

  with pytest.raises(ValidationError, match=expected_error):
    validate_gff3(gff3, fai)


def test_gff3_requires_version_directive(tmp_path):
  fai = write_file(tmp_path, "genome.fa.fai", "chr1\t100\t0\t100\t101\n")
  gff3 = write_file(
    tmp_path,
    "annotation.gff3",
    "chr1\tsource\tgene\t1\t50\t.\t+\t.\tID=gene1\n"
  )

  with pytest.raises(ValidationError, match="gff-version 3"):
    validate_gff3(gff3, fai)
