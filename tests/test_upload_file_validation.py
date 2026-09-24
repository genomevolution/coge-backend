import pytest

from model.exceptions.invalid_file_type import InvalidFileTypeException
from service.annotation_uploader_service import AnnotationUploaderService
from service.genome_uploader_service import GenomeUploaderService


@pytest.mark.parametrize("filename", ["genome.fa", "genome.FA", "genome.fa.gz", "genome.FA.GZ"])
def test_genome_upload_accepts_fa_and_fa_gz(filename):
  service = GenomeUploaderService(None, None)

  service._validate_file_extension(filename)


@pytest.mark.parametrize("filename", ["genome.fasta", "genome.fna", "genome.gz", "genome.txt"])
def test_genome_upload_rejects_other_extensions(filename):
  service = GenomeUploaderService(None, None)

  with pytest.raises(InvalidFileTypeException):
    service._validate_file_extension(filename)


@pytest.mark.parametrize("filename", ["annotation.gff3", "annotation.GFF3", "annotation.gff3.gz", "annotation.GFF3.GZ"])
def test_annotation_upload_accepts_gff3_and_gff3_gz(filename):
  service = AnnotationUploaderService(None, None, None)

  service._validate_file_extension(filename)


@pytest.mark.parametrize("filename", ["annotation.gff", "annotation.gz", "annotation.txt"])
def test_annotation_upload_rejects_other_extensions(filename):
  service = AnnotationUploaderService(None, None, None)

  with pytest.raises(InvalidFileTypeException):
    service._validate_file_extension(filename)
