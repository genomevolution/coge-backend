from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from service.nextflow_executor_service import NextflowExecutorService


@pytest.fixture
def executor_service(tmp_path: Path):
    service = NextflowExecutorService(
        work_dir=str(tmp_path / "work"),
        output_dir=str(tmp_path / "output"),
    )
    service.executor = MagicMock()
    return service


def assert_isolated_run(process_mock, service, execution_id):
    command = process_mock.call_args.args[0]
    expected_execution_dir = service.work_dir / execution_id

    assert process_mock.call_args.kwargs["cwd"] == str(expected_execution_dir)
    assert command[command.index("-work-dir") + 1] == str(expected_execution_dir / "work")
    assert "-resume" not in command


@patch("service.nextflow_executor_service.subprocess.Popen")
def test_genome_execution_uses_an_isolated_nextflow_session(process_mock, executor_service):
    process_mock.return_value.pid = 1001

    execution_id = executor_service.execute_genome_indexing(
        organism_id="organism-1",
        genome_id="genome-1",
        fasta_local_path="/tmp/genome.fasta",
    )

    assert_isolated_run(process_mock, executor_service, execution_id)


@patch("service.nextflow_executor_service.subprocess.Popen")
def test_annotation_execution_uses_an_isolated_nextflow_session(process_mock, executor_service):
    process_mock.return_value.pid = 1002

    execution_id = executor_service.execute_annotation_processing(
        organism_id="organism-1",
        genome_id="genome-1",
        annotation_id="annotation-1",
        gff3_local_path="/tmp/annotation.gff3",
    )

    assert_isolated_run(process_mock, executor_service, execution_id)
