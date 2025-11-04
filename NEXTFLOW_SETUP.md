# Nextflow Setup Guide for COGE Backend

This guide explains how to set up and use the Nextflow-based genome processing system.

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  Nextflow        │────▶│   Docker    │
│   Backend   │     │  Executor        │     │  Containers │
└─────────────┘     └──────────────────┘     └─────────────┘
       │                     │                       │
       │            ┌────────┴────────┐              │
       ▼            ▼                 ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌────────────┐ ┌─────────────┐
│  PostgreSQL │ │   Monitor    │ │   Work     │ │    MinIO    │
│  (Tracking) │ │   Service    │ │ Directory  │ │  (Storage)  │
│             │ │ (Auto-Finish)│ │(Temp Files)│ │             │
└─────────────┘ └──────────────┘ └────────────┘ └─────────────┘
```

## Setup Steps

### 1. Build Docker Images

```bash
# Build development image
docker compose build comparative-genomics-service-dev

# Or production image
docker compose build comparative-genomics-service-prod
```

### 2. Run Database Migration

```bash
# Apply the processing schema migration
docker compose --profile dev run --rm comparative-genomics-service-dev \
  sh -c "dbmate up"
```

Or manually if dbmate is installed:

```bash
dbmate --env dbmate.env up
```

### 3. Start Services

```bash
# Development
docker compose --profile dev up

# Production
docker compose --profile prod up
```

### 4. Verify Setup

Check that Nextflow is installed:

```bash
docker compose --profile dev exec comparative-genomics-service-dev nextflow -version
```

Check that Docker is accessible:

```bash
docker compose --profile dev exec comparative-genomics-service-dev docker ps
```

## Usage

### Upload FASTA File

Upload a FASTA file to automatically trigger indexing:

```bash
curl -X POST "http://localhost:8000/organisms/{organismId}/genomes/{genomeId}/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@genome.fa"
```

Response:

```json
{
  "message": "File uploaded successfully",
  "filePath": "organism-id/genomes/genome.fa",
  "fileUrl": "http://minio:9000/...",
  "fileType": "genome",
  "processingExecutionId": "uuid-here",
  "processingStatus": "RUNNING"
}
```

### Monitor Processing

Poll for status:

```bash
curl "http://localhost:8000/processing/executions/{executionId}"
```

Response:

```json
{
  "execution_id": "uuid",
  "status": "RUNNING",
  "progress": 50,
  "completed_tasks": 1,
  "total_tasks": 2,
  "genome_id": "genome-uuid",
  "organism_id": "organism-uuid",
  "started_at": "2025-11-03T10:00:00Z",
  "logs": "..recent log output.."
}
```

Status values:
- `RUNNING` - Pipeline is executing
- `COMPLETED` - Pipeline finished successfully
- `FAILED` - Pipeline encountered an error
- `CANCELLED` - Pipeline was manually stopped

### Automatic Finalization ✨

El sistema ahora **finaliza automáticamente** las ejecuciones completadas:

1. **Monitor Service** ejecuta cada 60 segundos
2. **Detecta** ejecuciones con status `COMPLETED`
3. **Automáticamente**:
   - Sube `.fa.gz`, `.fa.gz.gzi`, y `.fa.gz.fai` a MinIO
   - Crea registros en tabla `files`
   - Crea links en tabla `genome_files`
4. **Sin intervención manual necesaria** 🎉

### Finalize Manual (Opcional)

Si necesitas forzar la finalización sin esperar al monitor:

```bash
curl -X POST "http://localhost:8000/processing/executions/{executionId}/finalize"
```

### Cancel Execution

To stop a running pipeline:

```bash
curl -X DELETE "http://localhost:8000/processing/executions/{executionId}"
```

## Configuration

### Environment Variables

Set in `compose.yml`:

```yaml
environment:
  PROCESSING_TEMP_DIR: /tmp/genome_processing  # Temp file storage
```

### Nextflow Configuration

Edit `nextflow.config` to customize:

```groovy
process {
    withName: 'BGZIP_WITH_INDEX' {
        cpus = 4              # Number of CPUs
        memory = 8.GB         # Memory allocation
        time = 4.h            # Max execution time
    }
}
```

### Resource Requirements

Recommended for large genomes (100GB+):

```yaml
# In compose.yml
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 32G
    reservations:
      memory: 16G
```

## Directory Structure

```
/data/nextflow_work/     # Nextflow working directory
  ├── {execution-id}/
  │   ├── work/          # Temporary process files
  │   ├── report.html    # Execution report
  │   ├── trace.txt      # Process trace
  │   └── metadata.json  # Execution metadata

/data/nextflow_output/   # Pipeline output
  ├── {execution-id}/
  │   ├── genome.fa.gz
  │   ├── genome.fa.gz.gzi
  │   └── genome.fa.gz.fai

/tmp/genome_processing/  # Downloaded FASTAs
```

## Database Schema

The `processing.executions` table tracks all pipeline runs:

```sql
SELECT * FROM processing.executions 
WHERE genome_id = 'your-genome-id' 
ORDER BY created_at DESC;
```

Columns:
- `id` - Execution UUID
- `genome_id` - Associated genome
- `status` - Current status
- `progress` - Completion percentage
- `started_at`, `completed_at` - Timestamps
- `metadata` - Additional execution info (JSONB)

## Troubleshooting

### Issue: Pipeline stuck in RUNNING state

**Solution**: Check Nextflow logs:

```bash
docker compose --profile dev exec comparative-genomics-service-dev \
  cat /data/nextflow_work/{execution-id}/nextflow.log
```

### Issue: Docker permission denied

**Solution**: Ensure Docker socket is mounted and accessible:

```bash
# Check if Docker is accessible
docker compose --profile dev exec comparative-genomics-service-dev docker ps

# If not, check docker.sock permissions
ls -la /var/run/docker.sock
```

### Issue: Out of disk space

**Solution**: Clean up old executions:

```bash
# Remove old work directories
docker compose --profile dev exec comparative-genomics-service-dev \
  rm -rf /data/nextflow_work/*/work

# Remove old output files
docker compose --profile dev exec comparative-genomics-service-dev \
  rm -rf /data/nextflow_output/*
```

### Issue: Process killed by OOM

**Solution**: Increase memory limits in `nextflow.config` and `compose.yml`.

## Performance Optimization

### For Large Genomes (>50GB)

1. **Increase bgzip threads**:
   ```groovy
   cpus = 8  // In nextflow.config
   ```

2. **Allocate more memory**:
   ```groovy
   memory = 16.GB
   ```

3. **Use SSD for temp files**:
   Mount fast storage for `/tmp/genome_processing`

### For Multiple Concurrent Uploads

1. **Run dedicated Nextflow worker**:
   Add a separate service in `compose.yml` for processing

2. **Use queue system**:
   Switch profile to `slurm` or `k8s` for cluster execution

## Monitoring and Logs

### View Nextflow Logs

```bash
# Tail logs in real-time
docker compose --profile dev exec comparative-genomics-service-dev \
  tail -f /data/nextflow_work/{execution-id}/nextflow.log
```

### View Execution Report

After completion, download the HTML report:

```bash
# Report available at:
http://localhost:8000/files/download?filePath=...report.html
```

### Database Queries

```sql
-- Check all running executions
SELECT id, genome_id, progress, started_at 
FROM processing.executions 
WHERE status = 'RUNNING';

-- Check failed executions
SELECT id, error_message, completed_at 
FROM processing.executions 
WHERE status = 'FAILED';
```

## Production Deployment

### Recommended Setup

1. **Use external storage** for work directories
2. **Enable monitoring** with Nextflow Tower
3. **Configure backups** for execution metadata
4. **Set up alerts** for failed pipelines
5. **Use Kubernetes** for scalable execution

### External Cluster Execution

Edit `nextflow.config`:

```groovy
profiles {
    slurm {
        process.executor = 'slurm'
        process.queue = 'genomics-large'
        singularity.enabled = true
    }
}
```

Then use profile when starting execution:

```python
# In service
execution_id = self.nextflow_executor.execute_genome_indexing(
    organism_id=organismId,
    genome_id=genomeId,
    fasta_local_path=str(temp_fasta),
    profile="slurm"  # Use SLURM
)
```

## Support

For issues or questions:
- Check Nextflow documentation: https://www.nextflow.io/docs/latest/
- Review pipeline logs in `/data/nextflow_work/`
- Check database for execution status

