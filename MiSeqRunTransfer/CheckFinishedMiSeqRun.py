# coding=utf-8
import time
import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import Logger
import ParameterHandler

"""
Eric Fournier 2019-07-30
Script de transfert automatique des runs MiSeq terminées vers S:\\Partage\LSPQ_MiSeq

Procedure pour compiler avec pyinstaller:
    1- Copier les scripts CheckFinishedMiSeqRun.py, Logger.py et ParameterHandler.py dans C:\Users\foueri01\Documents\PyinstallerCompilation
    2- aller dans C:\Users\foueri01\Documents\PyinstallerCompilation avec une console ligne de commande
    3- Executer la commande suivante
            pyinstaller.exe --onefile --icon= CheckFinishedMiSeqRun.py
    4- L executable CheckFinishedMiSeqRun.exe sera dans C:\Users\foueri01\Documents\PyinstallerCompilation\Dist
            
"""

#Choisir le niveau de debuggage

#1 pour tester sur INSPQ-6499
#2 pour tester sur le Miseq
#3 pour production

#my_debug_level = 1

my_debug_level = int(raw_input("Enter un niveau de debugage:\n1 pour tester sur INSPQ-6499\n2 pour tester sur le Miseq\n3 pour production\n > "))

class Watcher:
    """
    Createur du watchdog et du handler
    """

    def __init__(self):
        #Le watchdog
        self.observer = Observer()

        # Parameters handler
        self.path_setter = ParameterHandler.PathSetter(my_debug_level)
        self.path_setter.OpenParamFile()
        self.path_setter.ParseParamFile()

        self.logfile = self.path_setter.GetLogginFile()

        # Le repertoire a scanner par le watchdog
        self.DIRECTORY_TO_WATCH =self.path_setter.GetMiSeqRootDir()

        self.path_setter.CloseParamFile()

    def run(self):
        """
        Pour demarrer le scan des runs MiSeq terminees
        :return:
        """
        event_handler = Handler(self.logfile)
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print "Error"

        self.observer.join()

class Handler(FileSystemEventHandler):
    """
    Class qui gere les taches de transfert de fichiers du MiSeq vers S:\\Partage\LSPQ_MiSeq

    """

    def __init__(self,logfile):
        self.ftl = Logger.FileTransferLogger(os.path.basename(__file__),logfile)

    def ExportToLspqMiSeqExperimental(self):
        '''
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\1_Experimental
        :return:
        '''

        #Export du SampleSheet.csv
        shutil.copy(self.MiSeqRunObj.GetSampleSheetPath(),os.path.join(self.LspqMiSeqRunObj.GetExpPath(),self.LspqMiSeqRunObj.GetNewSampleSheetName()))

    def ExportToLspqMiSeqSequenceBrute(self):
        '''
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\2_SequencesBrutes
        :return:
        '''

        #Export des fastq.gz
        for  fastq in os.listdir(self.MiSeqRunObj.GetBaseCallPath()):
            if(str(fastq).endswith('.fastq.gz')):
                fastq_from = os.path.join(self.MiSeqRunObj.GetBaseCallPath(),fastq)
                fastq_to = self.LspqMiSeqRunObj.GetSeqBrutPath()
                shutil.copy(fastq_from,fastq_to)

    def ExportToLspqMiSeqAnalyse(self):
        '''
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\3_Analyse

        :return:
        '''

        #Export du RunInfo.xml
        shutil.copy(self.MiSeqRunObj.GetRunInfoFilePath(),self.LspqMiSeqRunObj.GetAnalysePath())

        #Export du runParameters.xml
        shutil.copy(self.MiSeqRunObj.GetRunParameterFilePath(),self.LspqMiSeqRunObj.GetAnalysePath())

        #Export du repertoire InterOp
        shutil.copytree(self.MiSeqRunObj.GetInteropPath(),os.path.join(self.LspqMiSeqRunObj.GetAnalysePath(),'InterOp'))

    def SetNewRunName(self):
        '''
        On defini le nom de la run a partir de la quatrieme ligne du SampleSheet.csv
        :return:
        '''
        self.new_run_name = ""

        SampleSheetHandler = open(self.MiSeqRunObj.GetSampleSheetPath())
        SampleSheetHandler.readline()
        SampleSheetHandler.readline()
        SampleSheetHandler.readline()

        #La quatrieme ligne du SampleSheet a le format suivant 'Experiment Name,Date_Projet1-Projet2'
        self.new_run_name = SampleSheetHandler.readline()
        self.new_run_name = self.new_run_name.split(',')
        #Le nouveau nom du projet
        self.new_run_name = self.new_run_name[1].strip()

        SampleSheetHandler.close()

    def on_created(self, event):
        '''
        Execute lorsque le watchdog a detecter qu une run MiSeq est terminee
        :param event:
        :return:
        '''

        #Lorsqu une run MiSeq est terminee, le fichier CompletedJobInfo.xml est cree dans D:\Illumina\MiSeqOutput\IdDeLaRun
        if(isinstance(event,FileCreatedEvent)):
            if(event.src_path.endswith('CompletedJobInfo.xml')):
                # Parameters handler
                self.path_setter = ParameterHandler.PathSetter(my_debug_level)
                self.path_setter.OpenParamFile()
                self.path_setter.ParseParamFile()



                #path vers la run sur le MiSeq
                runpath = os.path.dirname(event.src_path)

                #Id de la run
                runname = os.path.basename(runpath)

                #Un object structure de la run terminee sur le MiSeq
                self.MiSeqRunObj = RunOnMiSeq(runpath)

                # Message affichee dans la console
                self.ftl.LogMessage("La run {0} est termine".format(runname))

                #Arborescence de la run sur le MiSeq
                self.MiSeqRunObj.SetPath()

                #On defini le nouveau nom de la run
                self.SetNewRunName()

                #Un object structure du nouveau repertoire d analyse a cree sur S:\\Partage\LSPQ_MiSeq\
                self.LspqMiSeqRunObj = RunOnPartageLspqMiSeq(self.new_run_name,self.path_setter.GetPartageLspqMiSeqRootDir())

                #Arborescence du repertoire d analyse a cree sur le S:\\Partage\LSPQ_MiSeq\
                self.LspqMiSeqRunObj.SetPath()

                self.ftl.LogMessage("Creation de l'arborescence de la run {new_runname} dans S:\Partage\LSPQ_MiSeq".format(new_runname = self.LspqMiSeqRunObj.GetRunName()))

                # On cree l arborescence du repertoire d analyse sur S:\\Partage\LSPQ_MiSeq\
                self.LspqMiSeqRunObj.CreatePath()

                self.ftl.LogMessage("Export des fichiers du MiSeq run {0} vers {1} en cours".format(runname,self.LspqMiSeqRunObj.GetRunPath()))

                #Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\1_Experimental
                self.ExportToLspqMiSeqExperimental()

                #Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\2_SequencesBrutes
                self.ExportToLspqMiSeqSequenceBrute()

                #Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\3_Analyse
                self.ExportToLspqMiSeqAnalyse()

                self.ftl.LogMessage("Export des fichiers du MiSeq run {0} vers {1} est termine\n ----------------------------------".format(runname, self.LspqMiSeqRunObj.GetRunPath()))

                self.path_setter.CloseParamFile()

                del self.MiSeqRunObj
                del self.LspqMiSeqRunObj
                del self.path_setter


class RunOnMiSeq():
    """
    Structure de la run terminee sur le MiSeq
    """
    def __init__(self,RunPath):
        pass
        self.runpath = RunPath

    def SetPath(self):
        '''
        Setting des paths
        :return:
        '''

        #path vers les fichiers fastq
        self.basecall_dir_path = os.path.join(self.runpath,'Data','Intensities','BaseCalls')

        #path vers le repertoire InterOp
        self.interop_dir_path = os.path.join(self.runpath,'InterOp')

        #path vers le fichier RunInfo.xml
        self.runinfo_file_path = os.path.join(self.runpath,'RunInfo.xml')

        #path vers le fichier run_Paramater.xml
        self.runParameters_file_path = os.path.join(self.runpath,'runParameters.xml')

        #path vers le SampleSheet.csv
        self.sampleSheet_file_path = os.path.join(self.runpath,'SampleSheet.csv')

    #Getters de path
    def GetBaseCallPath(self):
        return self.basecall_dir_path

    def GetInteropPath(self):
        return self.interop_dir_path

    def GetRunInfoFilePath(self):
        return self.runinfo_file_path

    def GetRunParameterFilePath(self):
        return self.runParameters_file_path

    def GetSampleSheetPath(self):
        return self.sampleSheet_file_path

class RunOnPartageLspqMiSeq():
    """
    Structure du nouveau repertoire d analyse sur  terminee sur S:\\Partage\LSPQ_MiSeq\
    """

    def __init__(self,RunName,basedir):

        #Nom de la run
        self.runname = RunName

        #S:\\Partage\LSPQ_MiSeq\
        self.basedir = basedir

        #path vers le nouveau repertoire d analyse sur S:\\Partage\LSPQ_MiSeq\
        self.runpath = os.path.join(self.basedir,self.runname)

        #nouveau nom de la SampleSheet.csv a definir
        self.SampleSheetName = ""

        #Definir le nouveau nom du SampleSheet.csv
        self.SetNewSampleSheetName()

    def SetPath(self):
        self.experimental_path = os.path.join(self.runpath,'1_Experimental')
        self.sequences_brutes_path = os.path.join(self.runpath,'2_SequencesBrutes')
        self.analyse_path = os.path.join(self.runpath,'3_Analyse')

    def CreatePath(self):
        '''
        Setting des paths de la nouvelle run sur S:\\Partage\LSPQ_MiSeq\
        :return:
        '''

        #Creation du repertoire racine
        os.makedirs(self.runpath)

        #Creation du sous repertoire 1_Experimental
        os.makedirs(self.experimental_path)

        #Creation du sous repertoire 2_SequencesBrutes
        os.makedirs(self.sequences_brutes_path)

        #Creation du sous repertoire 3_Analyse
        os.makedirs(self.analyse_path)

        #Creation des sous repertoires de project dans 3_Analyse
        self.CreateProjectSubDir()

    #Getter des path
    def GetExpPath(self):
        return self.experimental_path

    def GetSeqBrutPath(self):
        return self.sequences_brutes_path

    def GetAnalysePath(self):
        return self.analyse_path

    def GetNewSampleSheetName(self):
        return  self.SampleSheetName

    def GetRunName(self):
        return self.runname

    def GetRunPath(self):
        return self.runpath

    def CreateProjectSubDir(self):
        '''
        Creation des sous repertoires de project dans 3_Analyse
        :return:
        '''

        #Parsing du nom de la run pour obtenir la liste des noms de projets
        make_subdir_path = lambda x:os.path.join(self.analyse_path,x)
        subdir_list = str(self.GetRunName()).split('_')[1].split('-')
        subdir_path_list = map(make_subdir_path,subdir_list)

        #creation des sous repertoires de projet
        map(os.mkdir,subdir_path_list)

    def SetNewSampleSheetName(self):
        '''
        Setting du nouveau nom de la SampleSheet.csv a partir du nom de la run
        :return:
        '''
        self.SampleSheetName = self.runname + ".csv"

if __name__ == '__main__':
    w = Watcher()
    w.run()



