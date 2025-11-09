#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
 * Genome Indexing Pipeline
 * Generates .gz, .gzi and .fai files for JBrowse visualization
 */

params.fasta_file = ""
params.organism_id = ""
params.genome_id = ""
params.output_dir = "results"

log.info """\
    GENOME INDEXING PIPELINE
    ========================
    FASTA file     : ${params.fasta_file}
    Organism ID    : ${params.organism_id}
    Genome ID      : ${params.genome_id}
    Output dir     : ${params.output_dir}
    """
    .stripIndent()

process BGZIP_WITH_INDEX {
    tag "${genome_id}"
    
    cpus 4
    memory '8 GB'
    time '4h'
    
    publishDir "${params.output_dir}", mode: 'copy'
    
    input:
    path fasta
    val genome_id
    
    output:
    path "${genome_id}.fa.gz", emit: compressed
    path "${genome_id}.fa.gz.gzi", emit: gzi_index
    
    script:
    """
    # Use bgzip with index generation and multiple threads
    bgzip -c -i -@ ${task.cpus} ${fasta} > ${genome_id}.fa.gz
    """
}

process SAMTOOLS_FAIDX {
    tag "${genome_id}"
    
    memory '4 GB'
    time '2h'
    
    publishDir "${params.output_dir}", mode: 'copy'
    
    input:
    path fasta_gz
    val genome_id
    
    output:
    path "${genome_id}.fa.gz.fai", emit: fai_index
    
    script:
    """
    # Generate FASTA index
    samtools faidx ${fasta_gz}
    """
}

workflow {
    // Validate inputs
    if (!params.fasta_file) {
        error "Missing required parameter: --fasta_file"
    }
    if (!params.genome_id) {
        error "Missing required parameter: --genome_id"
    }
    
    // Create channels
    fasta_ch = Channel.fromPath(params.fasta_file, checkIfExists: true)
    genome_id_ch = Channel.value(params.genome_id)
    
    // Execute pipeline
    BGZIP_WITH_INDEX(fasta_ch, genome_id_ch)
    SAMTOOLS_FAIDX(BGZIP_WITH_INDEX.out.compressed, genome_id_ch)
    
    // Emit completion signal
    BGZIP_WITH_INDEX.out.compressed
        .concat(BGZIP_WITH_INDEX.out.gzi_index)
        .concat(SAMTOOLS_FAIDX.out.fai_index)
        .collect()
        .view { files -> 
            log.info "Pipeline completed successfully!"
            log.info "Generated files: ${files.join(', ')}"
        }
}

workflow.onComplete {
    log.info "Pipeline execution completed at: ${workflow.complete}"
    log.info "Execution status: ${workflow.success ? 'SUCCESS' : 'FAILED'}"
    log.info "Duration: ${workflow.duration}"
}

workflow.onError {
    log.error "Pipeline execution failed: ${workflow.errorMessage}"
}

