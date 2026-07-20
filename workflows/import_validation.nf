#!/usr/bin/env nextflow
nextflow.enable.dsl=2

params.validation_type = ""
params.input_file = ""
params.fai_file = ""
params.import_id = ""
params.output_dir = "results"

process VALIDATE_FASTA {
    tag "${params.import_id}"
    memory '1 GB'
    time '30m'
    publishDir "${params.output_dir}", mode: 'copy'

    input:
    path input_file

    output:
    path "validation.json"

    script:
    """
    python3 ${projectDir}/scripts/validate_import.py \\
      --type FASTA \\
      --input ${input_file} \\
      --report validation.json
    """
}

process VALIDATE_GFF3 {
    tag "${params.import_id}"
    memory '1 GB'
    time '30m'
    publishDir "${params.output_dir}", mode: 'copy'

    input:
    path input_file
    path fai_file

    output:
    path "validation.json"

    script:
    """
    gt gff3validator ${input_file}
    python3 ${projectDir}/scripts/validate_import.py \\
      --type GFF3 \\
      --input ${input_file} \\
      --fai ${fai_file} \\
      --report validation.json
    """
}

workflow {
    if (!params.input_file) {
        error "Missing required parameter: --input_file"
    }
    input_ch = channel.fromPath(params.input_file, checkIfExists: true)

    if (params.validation_type == "FASTA") {
        VALIDATE_FASTA(input_ch)
    } else if (params.validation_type == "GFF3") {
        if (!params.fai_file) {
            error "Missing required parameter: --fai_file"
        }
        fai_ch = channel.fromPath(params.fai_file, checkIfExists: true)
        VALIDATE_GFF3(input_ch, fai_ch)
    } else {
        error "Unsupported validation type: ${params.validation_type}"
    }
}
