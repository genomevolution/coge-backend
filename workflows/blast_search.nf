#!/usr/bin/env nextflow
nextflow.enable.dsl=2

params.query_file = ""
params.database_manifest = ""
params.output_dir = "results"
params.max_target_seqs = 50
params.evalue = 1e-5

process BLAST_AGAINST_GENOME {
    tag "${genome_id}"

    cpus 2
    memory '4 GB'
    time '4h'
    maxForks 4

    publishDir "${params.output_dir}", mode: 'copy'

    input:
    tuple val(genome_id), val(database_prefix)
    path query

    output:
    path "${genome_id}.tsv", emit: hits

    script:
    """
    blastn \\
      -query ${query} \\
      -db ${database_prefix} \\
      -evalue ${params.evalue} \\
      -max_target_seqs ${params.max_target_seqs} \\
      -outfmt '6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore qlen slen qseq sseq' \\
      -out ${genome_id}.raw.tsv
    awk -v genome_id="${genome_id}" '{print genome_id "\\t" \$0}' "${genome_id}.raw.tsv" > "${genome_id}.tsv"
    """
}

process MERGE_BLAST_RESULTS {
    tag "merge-blast-results"

    cpus 1
    memory '1 GB'

    publishDir "${params.output_dir}", mode: 'copy'

    input:
    path hit_files

    output:
    path 'blast_results.tsv', emit: results

    script:
    """
    if ls ${hit_files.join(' ')} >/dev/null 2>&1; then
      cat ${hit_files.join(' ')} | sort -k12,12g | head -n ${params.max_target_seqs} > blast_results.tsv
    else
      : > blast_results.tsv
    fi
    """
}

workflow {
    if (!params.query_file) error "Missing required parameter: --query_file"
    if (!params.database_manifest) error "Missing required parameter: --database_manifest"

    query_ch = channel.value(file(params.query_file))
    db_ch = channel
        .fromPath(params.database_manifest, checkIfExists: true)
        .splitText()
        .map { line -> line.trim() }
        .filter { line -> line }
        .map { line ->
            def columns = line.split('\t')
            if (columns.size() < 2) {
                error "Invalid BLAST database manifest row: ${line}"
            }
            tuple(columns[0], columns[1])
        }

    BLAST_AGAINST_GENOME(db_ch, query_ch)
    MERGE_BLAST_RESULTS(BLAST_AGAINST_GENOME.out.hits.collect())
}
