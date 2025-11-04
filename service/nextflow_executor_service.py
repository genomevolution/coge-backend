import subprocess
import uuid
import json
import os
import signal
import threading
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NextflowExecutorService:
    def __init__(self, work_dir: str = "/data/nextflow_work", output_dir: str = "/data/nextflow_output"):
        self.work_dir = Path(work_dir)
        self.output_dir = Path(output_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir = Path(__file__).parent.parent / "workflows"
        self.config_file = Path(__file__).parent.parent / "nextflow.config"
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="nextflow-watcher")
    
    def execute_genome_indexing(
        self, 
        organism_id: str, 
        genome_id: str, 
        fasta_local_path: str,
        profile: str = "standard"
    ) -> str:
        """
        Execute Nextflow pipeline for genome indexing
        
        Args:
            organism_id: ID of the organism
            genome_id: ID of the genome
            fasta_local_path: Local path to the FASTA file
            profile: Nextflow profile to use (standard, docker, slurm, k8s)
        
        Returns:
            execution_id: Unique ID for tracking this execution
        """
        execution_id = str(uuid.uuid4())
        execution_dir = self.work_dir / execution_id
        execution_output_dir = self.output_dir / execution_id
        execution_dir.mkdir(exist_ok=True)
        execution_output_dir.mkdir(exist_ok=True)
        
        log_file = execution_dir / "nextflow.log"
        
        cmd = [
            "nextflow",
            "run",
            str(self.workflows_dir / "genome_indexing.nf"),
            "-c", str(self.config_file),
            "-profile", profile,
            "-work-dir", str(execution_dir / "work"),
            "--fasta_file", fasta_local_path,
            "--organism_id", organism_id,
            "--genome_id", genome_id,
            "--output_dir", str(execution_output_dir),
            "-with-report", str(execution_dir / "report.html"),
            "-with-trace", str(execution_dir / "trace.txt"),
            "-with-timeline", str(execution_dir / "timeline.html"),
            "-with-dag", str(execution_dir / "dag.html"),
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
            "fasta_path": fasta_local_path,
            "status": "RUNNING",
            "profile": profile,
            "log_file": str(log_file),
            "output_dir": str(execution_output_dir),
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error_message": None
        }
        
        with open(execution_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Launch thread to wait for process completion
        self.executor.submit(
            self._manage_execution_lifecycle,
            process,
            execution_id,
            execution_dir
        )
        
        logger.info(f"Started Nextflow execution {execution_id} with PID {process.pid}")
        
        return execution_id
    
    def get_execution_status(self, execution_id: str) -> Dict:
        """
        Get detailed status of a Nextflow execution
        
        Returns dict with status, progress, logs, and generated files
        """
        execution_dir = self.work_dir / execution_id
        metadata_file = execution_dir / "metadata.json"
        
        if not metadata_file.exists():
            return {"status": "NOT_FOUND", "error": "Execution not found"}
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if metadata.get("status") == "RUNNING":
            # Just update progress, lifecycle thread will handle finalization
            progress_info = self._parse_progress(execution_dir / "trace.txt")
            metadata["progress"] = progress_info["progress"]
            metadata["completed_tasks"] = progress_info["completed"]
            metadata["total_tasks"] = progress_info["total"]
        
        metadata["logs"] = self._get_recent_logs(execution_dir / "nextflow.log")
        
        if metadata.get("status") == "COMPLETED":
            metadata["generated_files"] = self._get_generated_files(
                Path(metadata["output_dir"]),
                metadata["genome_id"]
            )
        
        return metadata
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running Nextflow execution"""
        execution_dir = self.work_dir / execution_id
        metadata_file = execution_dir / "metadata.json"
        
        if not metadata_file.exists():
            return False
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        pid = metadata.get("pid")
        if pid and self._is_process_running(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                metadata["status"] = "CANCELLED"
                metadata["completed_at"] = datetime.utcnow().isoformat()
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return True
            except ProcessLookupError:
                return False
        
        return False
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _manage_execution_lifecycle(self, process: subprocess.Popen, execution_id: str, execution_dir: Path):
        """
        Thread that waits for Nextflow to complete and updates status.
        This runs in background and doesn't block the API.
        """
        try:
            logger.info(f"Lifecycle thread started for execution {execution_id}")
            
            # Wait for process to complete (blocks only this thread)
            returncode = process.wait()
            
            logger.info(f"Execution {execution_id} finished with returncode {returncode}")
            
            # Read metadata
            metadata_file = execution_dir / "metadata.json"
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Classify result by reading log ONCE
            self._finalize_execution_status(execution_dir, metadata, returncode)
            
            logger.info(f"Execution {execution_id} finalized with status: {metadata.get('status')}")
            
        except Exception as e:
            logger.error(f"Error in lifecycle thread for {execution_id}: {e}", exc_info=True)
            try:
                metadata_file = execution_dir / "metadata.json"
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                metadata["status"] = "FAILED"
                metadata["error_message"] = f"Lifecycle management error: {str(e)}"
                metadata["completed_at"] = datetime.utcnow().isoformat()
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except Exception:
                pass
    
    def _finalize_execution_status(self, execution_dir: Path, metadata: Dict, returncode: Optional[int] = None) -> None:
        """
        Determine final status by reading log ONCE.
        Called by lifecycle thread when process completes.
        """
        log_file = execution_dir / "nextflow.log"
        trace_file = execution_dir / "trace.txt"
        
        # Read log file once to determine status
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_content = f.read()
                
                # Check for success indicators
                if "Execution status: SUCCESS" in log_content or "Pipeline completed successfully" in log_content:
                    metadata["status"] = "COMPLETED"
                # Check for failure indicators
                elif "ERROR ~" in log_content or "Execution status: FAILED" in log_content:
                    metadata["status"] = "FAILED"
                    # Extract error message
                    error_lines = [l for l in log_content.split('\n') if 'ERROR' in l or 'Caused by:' in l]
                    if error_lines:
                        metadata["error_message"] = '\n'.join(error_lines[-5:])
                else:
                    # Fallback to returncode
                    if returncode == 0:
                        metadata["status"] = "COMPLETED"
                    else:
                        metadata["status"] = "FAILED"
                        metadata["error_message"] = f"Process exited with code {returncode}"
        else:
            metadata["status"] = "FAILED"
            metadata["error_message"] = "No log file found"
        
        # Add final progress
        if metadata["status"] == "COMPLETED":
            metadata["progress"] = 100
            progress_info = self._parse_progress(trace_file)
            metadata["completed_tasks"] = progress_info["total"]
            metadata["total_tasks"] = progress_info["total"]
        
        metadata["completed_at"] = datetime.utcnow().isoformat()
        metadata["returncode"] = returncode
        
        # Write updated metadata
        with open(execution_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _parse_progress(self, trace_file: Path) -> Dict:
        """Parse Nextflow trace file to calculate progress"""
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
    
    def _get_recent_logs(self, log_file: Path, lines: int = 50) -> str:
        """Get recent log lines from Nextflow execution"""
        if not log_file.exists():
            return ""
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception:
            return ""
    
    def _get_generated_files(self, output_dir: Path, genome_id: str) -> Dict[str, str]:
        """Get paths to generated files"""
        files = {
            "fasta_gz": None,
            "gzi_index": None,
            "fai_index": None
        }
        
        if not output_dir.exists():
            return files
        
        gz_file = output_dir / f"{genome_id}.fa.gz"
        gzi_file = output_dir / f"{genome_id}.fa.gz.gzi"
        fai_file = output_dir / f"{genome_id}.fa.gz.fai"
        
        if gz_file.exists():
            files["fasta_gz"] = str(gz_file)
        if gzi_file.exists():
            files["gzi_index"] = str(gzi_file)
        if fai_file.exists():
            files["fai_index"] = str(fai_file)
        
        return files
    
    def get_execution_report_path(self, execution_id: str) -> Optional[Path]:
        """Get path to HTML report for an execution"""
        report_path = self.work_dir / execution_id / "report.html"
        return report_path if report_path.exists() else None

