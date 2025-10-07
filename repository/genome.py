from repository.db import DB
from model.genome import Genome
from model.annotationEntity import AnnotationEntity
from model.biosample import Biosample
from model.exceptions.entityNotFoundException import EntityNotFoundException
from model.paginable import PAGINATION_LIMIT

class GenomeRepository:
  def __init__(self, db: DB):
    self.db = db

  def getGenomesList(self, prev: str, next: str) -> list[Genome]:
    query = "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id LIMIT %s;"
    params = (PAGINATION_LIMIT,)
    if next is not None:
      query = "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id WHERE genome.id > %s LIMIT %s;"
      params = (next, PAGINATION_LIMIT)
    elif prev is not None:
      query = "SELECT * FROM genome JOIN biosample ON genome.biosample_fk = biosample.id WHERE genome.id < %s ORDER BY genome.id DESC LIMIT %s;"
      params = (prev, PAGINATION_LIMIT)
    rows = self.db.fetchTuplesWithPlaceholders(query, params)
    if prev is not None:
      rows.reverse()

    return [
      Genome(result = r)
      for r in rows]

  
  def getGenome(self, id:str) -> Genome:
    rows = self.db.fetchTuplesWithPlaceholders(
      """SELECT
          g.id              AS genome_id,
          g.biosample_fk    AS genome_biosample_fk,
          g.prefix          AS genome_prefix,
          g.created_at      AS genome_created_at,
          g.name            AS genome_name,
          g.description     AS genome_description,
          g.public          AS genome_public,
          g.accesion_id     AS genome_accesion_id,

          b.id              AS biosample_id,
          b.name            AS biosample_name,
          b.user_fk         AS biosample_user_fk,
          b.tax_id          AS biosample_tax_id,
          b.metadata        AS biosample_metadata,
          b.created_at      AS biosample_created_at,
          b.species_name    AS biosample_species_name,

          a.id              AS annotation_id,
          a.fk_genome       AS annotation_fk_genome,
          a.created_at      AS annotation_created_at,
          a.name            AS annotation_name,
          a.description     AS annotation_description,
          a.public          AS annotation_public,
          a.primary_annotation AS annotation_primary_annotation,
          af_file.path        AS annotation_file_path,

          gf_paths.fasta_path AS genome_fasta_path,
          gf_paths.fai_path   AS genome_fai_path,
          gf_paths.gzi_path   AS genome_gzi_path
          

        FROM genome g
        JOIN biosample b
          ON b.id = g.biosample_fk
        LEFT JOIN annotations a
          ON a.fk_genome = g.id
        LEFT JOIN (
          SELECT
            gf.genome_fk,
            MAX(CASE WHEN gf.type = 'FASTA' THEN f.path END) AS fasta_path,
            MAX(CASE WHEN gf.type = 'FAI'   THEN f.path END) AS fai_path,
            MAX(CASE WHEN gf.type = 'GZI'   THEN f.path END) AS gzi_path
          FROM genome_files gf
          JOIN files f ON f.id = gf.file_fk
          GROUP BY gf.genome_fk
        ) gf_paths ON gf_paths.genome_fk = g.id
        LEFT JOIN annotation_files af
          ON af.annotation_fk = a.id
        LEFT JOIN files af_file
          ON af_file.id = af.file_fk
        WHERE g.id = %s;""",
      (id,)
    )
    if len(rows) < 1:
      raise EntityNotFoundException("Genome not found")
    r0 = rows[0]
    genome = Genome(result = r0)

    annotations = []
    for r in rows:
      annotation_data = r[15:]
      if any(annotation_data):
        annotations.append(AnnotationEntity(result = annotation_data))
    genome.annotations = annotations

    return genome
