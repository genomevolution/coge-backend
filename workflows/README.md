# Nextflow Workflows for COGE Backend

This directory contains Nextflow pipelines for genome processing tasks.

## Genome Indexing Pipeline

The `genome_indexing.nf` workflow generates index files required for JBrowse visualization:
- `.fa.gz` - Compressed FASTA using bgzip
- `.fa.gz.gzi` - Block gzip index
- `.fa.gz.fai` - FASTA index

### Requirements

- Nextflow (installed in Docker container)
- Docker (for running tool containers)
- Java 11+ (for Nextflow runtime)
- bgzip (from htslib)
- samtools

### Running the Pipeline

The pipeline is automatically triggered when uploading a FASTA file through the API endpoint:

```bash
POST /organisms/{organismId}/genomes/{genomeId}/upload
```

### Manual Execution

If you need to run the pipeline manually:

```bash
nextflow run workflows/genome_indexing.nf \
  --fasta_file /path/to/genome.fa \
  --genome_id "genome-uuid" \
  --organism_id "organism-uuid" \
  --output_dir results \
  -profile standard
```

### Execution Profiles

- `standard` - Local execution with Docker (default)
- `local` - Local execution with Docker
- `docker` - Docker-only execution
- `slurm` - Execution on SLURM cluster
- `k8s` - Execution on Kubernetes

### Monitoring Execution

Check execution status via API:

```bash
GET /processing/executions/{executionId}
```

Response includes:
- `status` - RUNNING, COMPLETED, FAILED, CANCELLED
- `progress` - Percentage completion (0-100)
- `logs` - Recent log output
- `generated_files` - Paths to output files (when completed)

### Finalizing Execution

After completion, finalize to upload files to MinIO and create database records:

```bash
POST /processing/executions/{executionId}/finalize
```

### Cancelling Execution

To cancel a running execution:

```bash
DELETE /processing/executions/{executionId}
```

## Pipeline Output

The pipeline generates:

1. **{genome_id}.fa.gz** - Block-compressed FASTA
2. **{genome_id}.fa.gz.gzi** - Block gzip index
3. **{genome_id}.fa.gz.fai** - FASTA index

Files are stored in MinIO at: `{organism_id}/genomes/{filename}`

## Performance Considerations

### Resource Requirements

For large genomes (e.g., 150GB plant genomes):

- **CPU**: 4 cores (bgzip uses multiple threads)
- **Memory**: 8-16 GB
- **Disk**: ~3x genome size for temporary files
- **Time**: 1-4 hours depending on genome size

### Configuration

Edit `nextflow.config` to adjust:

```groovy
process {
    withName: 'BGZIP_WITH_INDEX' {
        cpus = 4
        memory = { 8.GB * task.attempt }
        time = { 4.h * task.attempt }
    }
}
```

## Troubleshooting

### Pipeline Fails with Memory Error

Increase memory in `nextflow.config`:

```groovy
memory = { 16.GB * task.attempt }
```

### Docker Permission Denied

Ensure Docker socket is mounted in `compose.yml`:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### Execution Not Found

Ensure the processing database schema is migrated:

```bash
dbmate up
```

## Development

### Adding New Processes

1. Add process definition to `genome_indexing.nf`
2. Update `nextflow.config` with resource requirements
3. Update total process count in `NextflowExecutorService._parse_progress()`

### Testing Pipeline Locally

```bash
# Test with small genome
nextflow run workflows/genome_indexing.nf \
  --fasta_file test_data/small_genome.fa \
  --genome_id "test-001" \
  --organism_id "org-001" \
  --output_dir test_results
```

## References

- [Nextflow Documentation](https://www.nextflow.io/docs/latest/index.html)
- [JBrowse File Formats](https://jbrowse.org/jb2/docs/config_guide/#file-formats)
- [SAMtools Documentation](http://www.htslib.org/doc/samtools.html)

