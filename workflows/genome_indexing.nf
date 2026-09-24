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

process BGZIP_WITH_INDEX {
    tag "${genome_id}"
    
    cpus 4
    memory '4 GB'
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
    # Use explicit output names so Nextflow can track both generated files.
    bgzip -i -I ${genome_id}.fa.gz.gzi -o ${genome_id}.fa.gz -@ ${task.cpus} ${fasta}
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
    fasta_ch = channel.fromPath(params.fasta_file, checkIfExists: true)
    genome_id_ch = channel.value(params.genome_id)
    
    // Execute pipeline
    BGZIP_WITH_INDEX(fasta_ch, genome_id_ch)
    SAMTOOLS_FAIDX(BGZIP_WITH_INDEX.out.compressed, genome_id_ch)
}
