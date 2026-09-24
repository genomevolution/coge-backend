from unittest.mock import MagicMock

from repository.annotation import AnnotationRepository


def create_repository_with_session(session):
  database = MagicMock()
  database.get_session.return_value = session
  return AnnotationRepository(database)


def configure_genome_query(session):
  genome_query = MagicMock()
  genome_query.filter.return_value.with_for_update.return_value.first.return_value = MagicMock()
  return genome_query


def test_first_annotation_is_primary_even_when_not_requested():
  session = MagicMock()
  genome_query = configure_genome_query(session)
  annotation_lookup = MagicMock()
  annotation_lookup.filter.return_value.first.return_value = None
  session.query.side_effect = [genome_query, annotation_lookup]
  repository = create_repository_with_session(session)

  annotation = repository.create_annotation(
    genome_id="genome-1",
    name="v1",
    description="First annotation",
    public=True,
    primary_annotation=False
  )

  assert annotation.primary_annotation is True


def test_later_annotation_is_not_primary_by_default():
  session = MagicMock()
  genome_query = configure_genome_query(session)
  annotation_lookup = MagicMock()
  annotation_lookup.filter.return_value.first.return_value = MagicMock()
  session.query.side_effect = [genome_query, annotation_lookup]
  repository = create_repository_with_session(session)

  annotation = repository.create_annotation(
    genome_id="genome-1",
    name="v2",
    description="Second annotation",
    public=True,
    primary_annotation=False
  )

  assert annotation.primary_annotation is False


def test_explicit_later_primary_annotation_replaces_current_primary():
  session = MagicMock()
  genome_query = configure_genome_query(session)
  annotation_lookup = MagicMock()
  annotation_lookup.filter.return_value.first.return_value = MagicMock()
  primary_annotations = MagicMock()
  session.query.side_effect = [genome_query, annotation_lookup, primary_annotations]
  repository = create_repository_with_session(session)

  annotation = repository.create_annotation(
    genome_id="genome-1",
    name="v2",
    description="Replacement primary annotation",
    public=True,
    primary_annotation=True
  )

  assert annotation.primary_annotation is True
  primary_annotations.filter.return_value.update.assert_called_once_with(
    {annotation.__class__.primary_annotation: False},
    synchronize_session=False
  )
