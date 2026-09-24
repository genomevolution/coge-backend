from service.minio_service import MinIOService


def test_generate_genome_file_path():
  service = MinIOService.__new__(MinIOService)

  path = service.generate_genome_file_path("organism-1", "genome.fa.gz")

  assert path == "organism-1/genomes/genome.fa.gz"


def test_generate_annotation_file_path():
  service = MinIOService.__new__(MinIOService)

  path = service.generate_annotation_file_path(
    "annotation-1",
    "features.gff3.gz"
  )

  assert path == "annotation/annotation-1/features.gff3.gz"
