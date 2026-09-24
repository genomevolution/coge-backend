import pytest

from service.blast import BlastService


class FakeJob:
    def to_dict(self, include_results=False):
        return {"status": "QUEUED", "includeResults": include_results}


class FakeRepository:
    def __init__(self):
        self.created = None

    def get_targets_for_selection(self, selection):
        return [{"id": "genome-1", "fastaPath": "organism/genome.fa.gz"}]

    def create_job(self, **kwargs):
        self.created = kwargs
        return FakeJob()


def test_create_blast_job_normalizes_query_and_parameters():
    repository = FakeRepository()
    result = BlastService(repository).create_job({
        "query": "ATGC",
        "selection": {"mode": "IDS", "genomeIds": ["genome-1"]},
        "parameters": {"evalue": "1e-10", "maxTargetSeqs": "25"},
    })

    assert result["status"] == "QUEUED"
    assert repository.created["query_fasta"] == ">query\nATGC\n"
    assert repository.created["parameters"]["evalue"] == 1e-10
    assert repository.created["parameters"]["maxTargetSeqs"] == 25


def test_create_blast_job_rejects_multiple_fasta_records():
    with pytest.raises(ValueError, match="one FASTA"):
        BlastService(FakeRepository()).create_job({
            "query": ">a\nATGC\n>b\nATGC",
            "selection": {"mode": "IDS", "genomeIds": ["genome-1"]},
        })


def test_create_blast_job_requires_targets():
    repository = FakeRepository()
    repository.get_targets_for_selection = lambda selection: []
    with pytest.raises(ValueError, match="at least one"):
        BlastService(repository).create_job({
            "query": "ATGC",
            "selection": {"mode": "IDS", "genomeIds": ["missing"]},
        })
