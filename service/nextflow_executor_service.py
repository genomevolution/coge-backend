import subprocess
import uuid
import json
import os
import signal
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from config import config
from service.execution_status import ExecutionStatus, FileNames

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NextflowExecutorService:
    def __init__(self, work_dir: Optional[str] = None, output_dir: Optional[str] = None):
        self.work_dir = Path(work_dir if work_dir is not None else config.NEXTFLOW_WORK_DIR)
        self.output_dir = Path(output_dir if output_dir is not None else config.NEXTFLOW_OUTPUT_DIR)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir = Path(__file__).parent.parent / "workflows"
        self.config_file = Path(__file__).parent.parent / FileNames.NEXTFLOW_CONFIG.value
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="nextflow-watcher")
    
    def execute_genome_indexing(
        self, 
        organism_id: str, 
        genome_id: str, 
        fasta_local_path: str,
        profile: str = "standard"
    ) -> str:
        execution_id = str(uuid.uuid4())
        execution_dir = self.work_dir / execution_id
        execution_output_dir = self.output_dir / execution_id
        execution_dir.mkdir(exist_ok=True)
        execution_output_dir.mkdir(exist_ok=True)
        
        log_file = execution_dir / FileNames.NEXTFLOW_LOG.value
        
        cmd = [
            "nextflow",
            "run",
            str(self.workflows_dir / FileNames.GENOME_INDEXING_WORKFLOW.value),
            "-c", str(self.config_file),
            "-profile", profile,
            "-work-dir", str(execution_dir / "work"),
            "--fasta_file", fasta_local_path,
            "--organism_id", organism_id,
            "--genome_id", genome_id,
            "--output_dir", str(execution_output_dir),
            "-with-report", str(execution_dir / FileNames.REPORT.value),
            "-with-trace", str(execution_dir / FileNames.TRACE.value),
            "-with-timeline", str(execution_dir / FileNames.TIMELINE.value),
            "-with-dag", str(execution_dir / FileNames.DAG.value),
            "-resume"
        ]
        
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=str(self.workflows_dir.parent)
            )
        
        metadata = {
            "execution_id": execution_id,
            "pid": process.pid,
            "organism_id": organism_id,
            "genome_id": genome_id,
            "original_path": fasta_local_path,
            "status": ExecutionStatus.RUNNING.value,
            "profile": profile,
            "log_file": str(log_file),
            "output_dir": str(execution_output_dir),
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error_message": None
        }
        
        with open(execution_dir / FileNames.METADATA.value, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.executor.submit(
            self._manage_execution_lifecycle,
            process,
            execution_id,
            execution_dir
        )
        
        logger.info(f"Started Nextflow execution {execution_id} with PID {process.pid}")
        
        return execution_id
    
    def get_execution_status(self, execution_id: str) -> Dict:
        execution_dir = self.work_dir / execution_id
        metadata_file = execution_dir / FileNames.METADATA.value
        
        if not metadata_file.exists():
            return {"status": ExecutionStatus.NOT_FOUND.value, "error": "Execution not found"}
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if self._metadata_status_is(metadata, ExecutionStatus.RUNNING):
            self._update_running_progress(metadata, execution_dir)
        
        metadata["logs"] = self._get_recent_logs(execution_dir / FileNames.NEXTFLOW_LOG.value)
        
        if self._metadata_status_is(metadata, ExecutionStatus.COMPLETED):
            self._update_completed_files(metadata)
        
        return metadata
    
    def cancel_execution(self, execution_id: str) -> bool:
        execution_dir = self.work_dir / execution_id
        metadata_file = execution_dir / FileNames.METADATA.value
        
        if not metadata_file.exists():
            return False
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        pid = metadata.get("pid")
        if pid and self._is_process_running(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                metadata["status"] = ExecutionStatus.CANCELLED.value
                metadata["completed_at"] = datetime.utcnow().isoformat()
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return True
            except ProcessLookupError:
                return False
        
        return False
    
    def _is_process_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _metadata_status_is(self, metadata: Dict, status: ExecutionStatus) -> bool:
        return metadata.get("status") == status.value
    
    def _manage_execution_lifecycle(self, process: subprocess.Popen, execution_id: str, execution_dir: Path):
        try:
            logger.info(f"Lifecycle thread started for execution {execution_id}")
            
            returncode = process.wait()
            
            logger.info(f"Execution {execution_id} finished with returncode {returncode}")
            
            metadata_file = execution_dir / FileNames.METADATA.value
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            self._finalize_execution_status(execution_dir, metadata, returncode)
            
            logger.info(f"Execution {execution_id} finalized with status: {metadata.get('status')}")
            
        except Exception as e:
            logger.error(f"Error in lifecycle thread for {execution_id}: {e}", exc_info=True)
            try:
                metadata_file = execution_dir / FileNames.METADATA.value
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                metadata["status"] = ExecutionStatus.FAILED.value
                metadata["error_message"] = f"Lifecycle management error: {str(e)}"
                metadata["completed_at"] = datetime.utcnow().isoformat()
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except Exception:
                pass
    
    def _finalize_execution_status(self, execution_dir: Path, metadata: Dict, returncode: Optional[int] = None) -> None:
        log_file = execution_dir / FileNames.NEXTFLOW_LOG.value
        trace_file = execution_dir / FileNames.TRACE.value
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_content = f.read()
                
                if "Execution status: SUCCESS" in log_content or "Pipeline completed successfully" in log_content:
                    metadata["status"] = ExecutionStatus.COMPLETED.value
                elif "ERROR ~" in log_content or "Execution status: FAILED" in log_content:
                    metadata["status"] = ExecutionStatus.FAILED.value
                    error_lines = [l for l in log_content.split('\n') if 'ERROR' in l or 'Caused by:' in l]
                    if error_lines:
                        metadata["error_message"] = '\n'.join(error_lines[-5:])
                else:
                    if returncode == 0:
                        metadata["status"] = ExecutionStatus.COMPLETED.value
                    else:
                        metadata["status"] = ExecutionStatus.FAILED.value
                        metadata["error_message"] = f"Process exited with code {returncode}"
        else:
            metadata["status"] = ExecutionStatus.FAILED.value
            metadata["error_message"] = "No log file found"
        
        if self._metadata_status_is(metadata, ExecutionStatus.COMPLETED):
            metadata["progress"] = 100
            progress_info = self._parse_progress(trace_file)
            metadata["completed_tasks"] = progress_info["total"]
            metadata["total_tasks"] = progress_info["total"]
        
        metadata["completed_at"] = datetime.utcnow().isoformat()
        metadata["returncode"] = returncode
        
        with open(execution_dir / FileNames.METADATA.value, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _parse_progress(self, trace_file: Path) -> Dict:
        if not trace_file.exists():
            return {"progress": 0, "completed": 0, "total": 2}
        
        total_processes = 2
        completed = 0
        
        try:
            with open(trace_file, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    for line in lines[1:]:
                        if 'COMPLETED' in line:
                            completed += 1
        except Exception:
            pass
        
        progress = int((completed / total_processes) * 100) if total_processes > 0 else 0
        
        return {
            "progress": progress,
            "completed": completed,
            "total": total_processes
        }
    
    def _update_running_progress(self, metadata: Dict, execution_dir: Path) -> None:
        progress_info = self._parse_progress(execution_dir / FileNames.TRACE.value)
        metadata["progress"] = progress_info["progress"]
        metadata["completed_tasks"] = progress_info["completed"]
        metadata["total_tasks"] = progress_info["total"]
    
    def _update_completed_files(self, metadata: Dict) -> None:
        metadata["generated_files"] = self._get_generated_files(
            Path(metadata["output_dir"]),
            metadata["genome_id"]
        )
    
    def _get_recent_logs(self, log_file: Path, lines: int = 50) -> str:
        if not log_file.exists():
            return ""
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception:
            return ""
    
    def _get_generated_files(self, output_dir: Path, genome_id: str) -> Dict[str, str]:
        files = {
            "fasta_gz": None,
            "gzi_index": None,
            "fai_index": None
        }
        
        if not output_dir.exists():
            return files
        
        gz_file = output_dir / f"{genome_id}{FileNames.FASTA_GZ_EXTENSION.value}"
        gzi_file = output_dir / f"{genome_id}{FileNames.GZI_EXTENSION.value}"
        fai_file = output_dir / f"{genome_id}{FileNames.FAI_EXTENSION.value}"
        
        if gz_file.exists():
            files["fasta_gz"] = str(gz_file)
        if gzi_file.exists():
            files["gzi_index"] = str(gzi_file)
        if fai_file.exists():
            files["fai_index"] = str(fai_file)
        
        return files
    
    def get_execution_report_path(self, execution_id: str) -> Optional[Path]:
        report_path = self.work_dir / execution_id / FileNames.REPORT.value
        return report_path if report_path.exists() else None

