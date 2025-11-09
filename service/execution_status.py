from enum import Enum

class ExecutionStatus(str, Enum):
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'
    FINALIZED = 'FINALIZED'
    NOT_FOUND = 'NOT_FOUND'

class ExecutionType(str, Enum):
    GENOME_INDEXING = 'GENOME_INDEXING'
    ANNOTATION_PROCESSING = 'ANNOTATION_PROCESSING'

class FileNames(str, Enum):
    NEXTFLOW_LOG = 'nextflow.log'
    TRACE = 'trace.txt'
    METADATA = 'metadata.json'
    REPORT = 'report.html'
    TIMELINE = 'timeline.html'
    DAG = 'dag.html'
    GENOME_INDEXING_WORKFLOW = 'genome_indexing.nf'
    NEXTFLOW_CONFIG = 'nextflow.config'
    FASTA_GZ_EXTENSION = '.fa.gz'
    GZI_EXTENSION = '.fa.gz.gzi'
    FAI_EXTENSION = '.fa.gz.fai'

