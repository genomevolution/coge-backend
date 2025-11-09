#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
 * Annotation Processing Pipeline
 * Sorts, compresses, and indexes GFF3 files for JBrowse visualization
 */

params.gff3_file = ""
params.organism_id = ""
params.genome_id = ""
params.annotation_id = ""
params.output_dir = "results"

log.info """\
    ANNOTATION PROCESSING PIPELINE
    ==============================
    GFF3 file      : ${params.gff3_file}
    Organism ID    : ${params.organism_id}
    Genome ID      : ${params.genome_id}
    Annotation ID  : ${params.annotation_id}
    Output dir     : ${params.output_dir}
    """
    .stripIndent()

process SORT_GFF3 {
    tag "${annotation_id}"
    
    cpus 2
    memory '4 GB'
    time '2h'
    
    publishDir "${params.output_dir}", mode: 'copy'
    
    input:
    path gff3
    val annotation_id
    
    output:
    path "${annotation_id}.sorted.gff3", emit: sorted_gff3
    
    script:
    """
    # Sort and tidy GFF3 file using genometools
    gt gff3 -sortlines -retainids -tidy ${gff3} > ${annotation_id}.sorted.gff3
    """
}

process COMPRESS_GFF3 {
    tag "${annotation_id}"
    
    cpus 4
    memory '4 GB'
    time '2h'
    
    publishDir "${params.output_dir}", mode: 'copy'
    
    input:
    path sorted_gff3
    val annotation_id
    
    output:
    path "${annotation_id}.sorted.gff3.gz", emit: compressed_gff3
    
    script:
    """
    # Compress GFF3 file using bgzip with multiple threads
    bgzip -c -@ ${task.cpus} ${sorted_gff3} > ${annotation_id}.sorted.gff3.gz
    """
}

process INDEX_GFF3 {
    tag "${annotation_id}"
    
    memory '2 GB'
    time '1h'
    
    publishDir "${params.output_dir}", mode: 'copy'
    
    input:
    path compressed_gff3
    val annotation_id
    
    output:
    path "${annotation_id}.sorted.gff3.gz.tbi", emit: tabix_index
    
    script:
    """
    # Index compressed GFF3 file using tabix
    tabix -p gff ${compressed_gff3}
    """
}

workflow {
    // Validate inputs
    if (!params.gff3_file) {
        error "Missing required parameter: --gff3_file"
    }
    if (!params.annotation_id) {
        error "Missing required parameter: --annotation_id"
    }
    
    // Create channels
    gff3_ch = Channel.fromPath(params.gff3_file, checkIfExists: true)
    annotation_id_ch = Channel.value(params.annotation_id)
    
    // Execute pipeline
    SORT_GFF3(gff3_ch, annotation_id_ch)
    COMPRESS_GFF3(SORT_GFF3.out.sorted_gff3, annotation_id_ch)
    INDEX_GFF3(COMPRESS_GFF3.out.compressed_gff3, annotation_id_ch)
    
    // Emit completion signal
    SORT_GFF3.out.sorted_gff3
        .concat(COMPRESS_GFF3.out.compressed_gff3)
        .concat(INDEX_GFF3.out.tabix_index)
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

