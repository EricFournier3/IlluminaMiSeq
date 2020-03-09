from illuminate import InteropDataset
import glob
import os
import gzip
import sys


#Modif_20200306


class FastqReader:
    """
    Pour lecture de fichier fastq
    """
    def __init__(self, fname):
        self.__file = None
        self.__gz = False
        self.__eof = False
        self.filename = fname
        if self.filename.endswith(".gz"):
            self.__gz = True
            self.__file = gzip.open(self.filename, "r")
        else:
            self.__gz = False
            self.__file = open(self.filename, "r")
        if self.__file == None:
            print("Failed to open file " + self.filename)
            sys.exit(1)

    def __del__(self):
        if self.__file != None:
            self.__file.close()

    def nextRead(self):
        if self.__eof == True or self.__file == None:
            return None

        lines = []
        # read 4 (lines, name, sequence, strand, quality)
        for i in xrange(0, 4):
            line = self.__file.readline().rstrip()
            if len(line) == 0:
                self.__eof = True
                return None
            lines.append(line)
        return lines

    def isEOF(self):
        return False

class MiSeqStatComputer():
    """
    Calculateur de statistiques MiSeq
    """

    def __init__(self,run_path,lspq_miseq_dir_path):
        pass
        self.run_path = run_path
        self.lspq_miseq_dir_path = lspq_miseq_dir_path
        self.cluster_passing_filter = 0
        self.cluster_density_ = 0
        self.perc_over_q30 = 0

        self.Dataset = InteropDataset(self.run_path)
        self.experiment_name = self.Dataset.Metadata().experiment_name

        self.r1_samples_qual = {}
        self.r2_samples_qual = {}

        self.total_nb_reads = 0


    def ComputeRunStat(self):
        """
        Statistiques de la run
        :return:
        """
        qualitymetrics = self.Dataset.QualityMetrics()
        tilemetrics = self.Dataset.TileMetrics()
        #print qualitymetrics.read_qscore_results['q30']
        #print qualitymetrics.read_qscore_results.__str__()
        #print qualitymetrics.read_config

        self.perc_over_q30 = round((float(qualitymetrics.read_qscore_results['q30'][0]) + float(qualitymetrics.read_qscore_results['q30'][3]))/2,1)

        cluster_density = tilemetrics.mean_cluster_density
        self.cluster_density_ = round(float(cluster_density)/1000,1)

        self.cluster_passing_filter = round(float(tilemetrics.mean_cluster_density_pf)/float(cluster_density),3) * 100

    def qual_stat(self,qstr):
        """
        Nombre de base ayant une valeur de qualite superieur a Q30
        :param qstr:
        :return:
        """
        q30 = 0
        for q in qstr:
            qual = ord(q) - 33
            if qual >= 30:
                q30 += 1
        return q30


    def ComputeSamplesStat(self):
        """
        Calcul de statistique par sample
        :return:
        """

        for fastq in glob.glob(os.path.join(self.run_path,'Data','Intensities','BaseCalls',"*.fastq.gz")):
            sample_name = os.path.basename(fastq).split('_')[0]
            sens = os.path.basename(fastq).split('_')[3]

            fastq_reader = FastqReader(fastq)
            total_count = 0
            q30_count = 0
            nb_read = 0

            while True:
                read = fastq_reader.nextRead()
                if read == None:
                    break
                nb_read += 1
                total_count += len(read[3])
                q30 = self.qual_stat(read[3])
                q30_count += q30

            del(fastq_reader)

            self.total_nb_reads += nb_read

            if sens == "R1":
                self.r1_samples_qual[sample_name] = {}
                self.r1_samples_qual[sample_name]['nb_read'] = str(nb_read)
                self.r1_samples_qual[sample_name]['q30_perc'] = (round(100 * float(q30_count) / float(total_count),1))
            else:
                self.r2_samples_qual[sample_name] = {}
                self.r2_samples_qual[sample_name]['nb_read'] = str(nb_read)
                self.r2_samples_qual[sample_name]['q30_perc'] = (round(100 * float(q30_count) / float(total_count), 1))

    def WriteStat(self):
        """
        Enregistrer les statistiques dans un fichier
        :return:
        """
        stat_file = os.path.join(self.lspq_miseq_dir_path,'2_MiSeqRunTrace',self.experiment_name.split('_')[2],'FinalMiSeqStat_' + self.experiment_name + ".txt")

        with open(stat_file,'w') as stat_file_handle:
            stat_file_handle.write("ID\tNb_Reads\tCluster_Density_K_mm2\tCluster_Passing_Filter	Over_Q30\tR1_R2_Mean_Q30\n")

            for sample in self.r1_samples_qual.keys():
                mean_q30 = str(round((float(self.r1_samples_qual[sample]['q30_perc']) + float(self.r2_samples_qual[sample]['q30_perc'])) / 2,2))
                stat_file_handle.write(sample + '_R1\t' + str(self.r1_samples_qual[sample]['nb_read']) + '\t' + 'NA\t' + 'NA\t' + str(self.r1_samples_qual[sample]['q30_perc']) + '\t' + mean_q30 + '\n')
                stat_file_handle.write(sample + '_R2\t' + str(self.r2_samples_qual[sample]['nb_read']) + '\t' + 'NA\t' + 'NA\t' + str(self.r2_samples_qual[sample]['q30_perc']) + '\t ' + '\n')

            stat_file_handle.write('RUN\t' + str(self.total_nb_reads) + '\t' + str(self.cluster_density_) + '\t' + str(self.cluster_passing_filter) + '\t' + str(self.perc_over_q30) + '\t ' + '\n')

    def GetPercOverQ30(self):
        return  self.perc_over_q30

    def GetClusterDensity(self):
        return self.cluster_density_

