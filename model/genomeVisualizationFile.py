
class GenomeVisualizationFile:
    def __init__(self, result: tuple):
        print(result)
        self.fasta_file_path = result[0]
        self.fai_file_path = result[1]
        self.gzi_file_path = result[2]
