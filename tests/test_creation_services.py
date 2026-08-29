import pytest

from model.exceptions.duplicate_entity import DuplicateEntityException
from model.exceptions.entity_not_found import EntityNotFoundException
from service.annotation import AnnotationService
from service.genome import GenomeService
from service.organism import OrganismService
from service.source import SourceService


class FakeEntity:
  def __init__(self, **values):
    self.values = values
    self.id = values.get("id")

  def to_dict(self, **_kwargs):
    return self.values


class FakeOrganismRepository:
  def __init__(self, existing_organism=None):
    self.created = None
    self.existing_organism = existing_organism

  def find_organism_by_identity(self, name, tax_id, species_name):
    return self.existing_organism

  def create_organism(self, name, tax_id, species_name, metadata=None):
    self.created = {
      "name": name,
      "tax_id": tax_id,
      "species_name": species_name,
      "metadata": metadata
    }
    return FakeEntity(
      id="organism-1",
      name=name,
      taxId=tax_id,
      speciesName=species_name,
      metadata=metadata
    )


class FakeGenomeRepository:
  def __init__(self, organism_exists=True):
    self.organism_exists = organism_exists
    self.created = None

  def create_genome(self, organism_id, name, description, public, accession_id, source_id=None):
    if not self.organism_exists:
      raise EntityNotFoundException("Organism not found")

    self.created = {
      "organism_id": organism_id,
      "name": name,
      "description": description,
      "public": public,
      "accession_id": accession_id,
      "source_id": source_id
    }
    return FakeEntity(
      id="genome-1",
      name=name,
      description=description,
      public=public,
      accesionId=accession_id
    )


class FakeAnnotationRepository:
  def __init__(self, genome_exists=True):
    self.genome_exists = genome_exists
    self.created = None

  def get_annotation_by_id(self, _id):
    return FakeEntity(id=_id)

  def create_annotation(self, genome_id, name, description, public, primary_annotation):
    if not self.genome_exists:
      raise EntityNotFoundException("Genome not found")

    self.created = {
      "genome_id": genome_id,
      "name": name,
      "description": description,
      "public": public,
      "primary_annotation": primary_annotation
    }
    return FakeEntity(
      id="annotation-1",
      name=name,
      description=description,
      public=public,
      primaryAnnotation=primary_annotation
    )


class FakeSourceRepository:
  def get_sources(self):
    return [
      FakeEntity(id="source-1", name="NCBI"),
      FakeEntity(id="source-2", name="Universidad de Los Andes - Colombia"),
    ]


class FakeUploaderService:
  def __init__(self):
    self.uploaded = None

  def upload_annotation_file(self, genome_id, annotation_id, file):
    self.uploaded = (genome_id, annotation_id, file)
    return "upload-result"


def test_create_organism_with_valid_fields():
  repository = FakeOrganismRepository()
  service = OrganismService(repository)

  result = service.create_organism({
    "name": "LL0772",
    "taxId": "5679",
    "speciesName": "Leishmania panamensis",
    "metadata": {"host": "Homo sapiens"}
  })

  assert result["id"] == "organism-1"
  assert repository.created["name"] == "LL0772"
  assert repository.created["metadata"] == {"host": "Homo sapiens"}


@pytest.mark.parametrize("missing_field", ["name", "taxId", "speciesName"])
def test_create_organism_rejects_missing_required_fields(missing_field):
  service = OrganismService(FakeOrganismRepository())
  payload = {
    "name": "LL0772",
    "taxId": "5679",
    "speciesName": "Leishmania panamensis"
  }
  payload[missing_field] = ""

  with pytest.raises(ValueError):
    service.create_organism(payload)


def test_create_organism_rejects_duplicate_identity():
  repository = FakeOrganismRepository(existing_organism=FakeEntity(id="organism-1"))
  service = OrganismService(repository)

  with pytest.raises(DuplicateEntityException):
    service.create_organism({
      "name": "UN0010",
      "taxId": "5660",
      "speciesName": "Leishmania braziliensis"
    })

  assert repository.created is None


def test_create_genome_for_existing_organism():
  repository = FakeGenomeRepository()
  service = GenomeService(repository, FakeUploaderService())

  result = service.create_genome("organism-1", {
    "name": "v1",
    "description": "Assembly description",
    "accessionId": "GCA_1",
    "sourceId": "source-1",
    "public": True
  })

  assert result["id"] == "genome-1"
  assert repository.created["organism_id"] == "organism-1"
  assert repository.created["source_id"] == "source-1"


def test_create_genome_rejects_missing_organism():
  service = GenomeService(FakeGenomeRepository(organism_exists=False), FakeUploaderService())

  with pytest.raises(EntityNotFoundException):
    service.create_genome("missing-organism", {
      "name": "v1",
      "description": "Assembly description",
      "accessionId": "GCA_1",
      "sourceId": "source-1",
      "public": True
    })


def test_create_annotation_for_existing_genome():
  repository = FakeAnnotationRepository()
  service = AnnotationService(repository, FakeUploaderService())

  result = service.create_annotation("genome-1", {
    "name": "v1",
    "description": "Companion annotation",
    "public": True,
    "primaryAnnotation": True
  })

  assert result["id"] == "annotation-1"
  assert repository.created["genome_id"] == "genome-1"
  assert repository.created["primary_annotation"] is True


def test_create_annotation_rejects_missing_genome():
  service = AnnotationService(
    FakeAnnotationRepository(genome_exists=False),
    FakeUploaderService()
  )

  with pytest.raises(EntityNotFoundException):
    service.create_annotation("missing-genome", {
      "name": "v1",
      "description": "Companion annotation",
      "public": True,
      "primaryAnnotation": False
    })


def test_annotation_upload_is_delegated_to_uploader_service():
  uploader = FakeUploaderService()
  service = AnnotationService(FakeAnnotationRepository(), uploader)
  uploaded_file = object()

  result = service.upload_annotation_file(
    "genome-1",
    "annotation-1",
    uploaded_file
  )

  assert result == "upload-result"
  assert uploader.uploaded == ("genome-1", "annotation-1", uploaded_file)


def test_list_sources():
  service = SourceService(FakeSourceRepository())

  result = service.get_sources()

  assert result == [
    {"id": "source-1", "name": "NCBI"},
    {"id": "source-2", "name": "Universidad de Los Andes - Colombia"},
  ]
