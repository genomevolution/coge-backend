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
    ANNOTATION_PROCESSING_WORKFLOW = 'annotation_processing.nf'
    IMPORT_VALIDATION_WORKFLOW = 'import_validation.nf'
    NEXTFLOW_CONFIG = 'nextflow.config'
    FASTA_GZ_EXTENSION = '.fa.gz'
    GZI_EXTENSION = '.fa.gz.gzi'
    FAI_EXTENSION = '.fa.gz.fai'
    SORTED_GFF3_EXTENSION = '.sorted.gff3'
    GFF3_GZ_EXTENSION = '.sorted.gff3.gz'
    TABIX_EXTENSION = '.sorted.gff3.gz.tbi'
