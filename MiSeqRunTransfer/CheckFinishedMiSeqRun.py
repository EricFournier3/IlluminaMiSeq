# coding=utf-8
import time
import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import Logger
import ParameterHandler
import re

"""
Eric Fournier 2019-07-30
Script de transfert automatique des runs MiSeq terminées vers S:\\Partage\LSPQ_MiSeq

Procedure pour compiler avec pyinstaller:
    1- Copier les scripts CheckFinishedMiSeqRun.py, Logger.py et ParameterHandler.py dans C:\Users\foueri01\Documents\PyinstallerCompilation
    2- aller dans C:\Users\foueri01\Documents\PyinstallerCompilation avec une console ligne de commande
    3- Executer la commande suivante
            pyinstaller.exe --onefile --icon=watchdog.ico CheckFinishedMiSeqRun.py
    4- L executable CheckFinishedMiSeqRun.exe sera dans C:\Users\foueri01\Documents\PyinstallerCompilation\Dist
    5-  Pour voir l executable avec le nouvel icone, il faut le copier dans un autre repertoire
            
"""

#Choisir le niveau de debuggage
my_debug_level = int(raw_input("Enter un niveau de debugage:\n1 pour tester sur INSPQ-6499 disque I\n2 pour tester sur INSPQ-6499 disque J\n3 pour production sur INSPQ-8719\n4 pour production sur INSPQ-8900\n > "))

if (my_debug_level == 1):
    print "INSPQ-6499 disque I"

elif (my_debug_level == 2):
    print "INSPQ-6499 disque J"

elif (my_debug_level == 3):
    print "pour production sur INSPQ-8719"

elif(my_debug_level == 4):
    print "pour production sur INSPQ-8900"

else:
    print "Choix invalide"
    exit()


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
        self.irida_samples_in_run = False

    def ExportToLspqMiSeqExperimental(self):
        '''
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\1_Experimental
        :return:
        '''

        #Export du SampleSheet.csv
        shutil.copy(self.MiSeqRunObj.GetSampleSheetPath(),os.path.join(self.LspqMiSeqRunObj.GetExpPath(),self.LspqMiSeqRunObj.GetNewSampleSheetName()))

    def ExportToLspqMiSeqMiSeqRunTrace(self):
        """
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\2_MiSeqRunTrace
        :return:
        """
        # Export du RunInfo.xml
        shutil.copy(self.MiSeqRunObj.GetRunInfoFilePath(), self.LspqMiSeqRunObj.GetMiseqRunTraceCartridge())

        # Export du runParameters.xml
        shutil.copy(self.MiSeqRunObj.GetRunParameterFilePath(), self.LspqMiSeqRunObj.GetMiseqRunTraceCartridge())

        # Export du repertoire InterOp
        shutil.copytree(self.MiSeqRunObj.GetInteropPath(),os.path.join(self.LspqMiSeqRunObj.GetMiseqRunTraceCartridge(), 'InterOp'))

    def ExportToLspqMiSeqSequenceBrute(self):
        '''
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\3_SequencesBrutes
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
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\4_Analyse

        :return:
        '''
        pass

    def CreateIridaSampleSheet(self):
        """
        On cree dans le repertoire racine de la run sur le MiSeq, un
        SampleSheet.csv qui contient seulement des specimens irida
        :return:
        """
        self.MiSeqRunObj.CreateIridaSampleSheet()

    def CheckIfIridaSamplesInRun(self):
        if re.search('pulsenet',self.new_run_name):
            return True

        return False

    def ImportIridaUploaderInfoFile(self):
        """
        Fichier .miseqUploaderInfo avec status a Complete pour ne pas que le irida scan cette run
        :return:
        """

        shutil.copy(self.path_setter.GetIridaUploaderInfoFile(),self.MiSeqRunObj.GetRunPath())

    def ConcatSampleSheet(self):
        """
        Concatenation des sample sheets
        :return:
        """

        first_cartridge = False

        sample_sheet_path=os.path.join(self.LspqMiSeqRunObj.GetExpPath(), self.LspqMiSeqRunObj.GetNewSampleSheetName())
        #print sample_sheet_path #U:\TEMP\LSPQ_MiSeq\11111111_test1-test2\1_Experimental\11111111_test1-test2_C1.csv

        # nom du sample sheet de cette cassette
        sample_sheet_name = self.LspqMiSeqRunObj.GetNewSampleSheetName()[:-4]

        # on extrait le nom de la run et celui de la cassette
        search_obj = re.search(r'^(\S+_\S+)_(\S+)$', sample_sheet_name)
        run_name = search_obj.group(1)
        cartridge_name = search_obj.group(2)

        # nom du sample sheet concatene sans l extension csv
        concat_sample_sheet_name = run_name

        concat_sample_sheet_exist = os.path.isfile(os.path.join(self.LspqMiSeqRunObj.GetExpPath(),concat_sample_sheet_name + '.csv'))

        # on verifie si le sample sheet concat existe deja
        if not concat_sample_sheet_exist:
            first_cartridge = True

        concat_file_handler = open(os.path.join(self.LspqMiSeqRunObj.GetExpPath(), concat_sample_sheet_name + '.csv'),'a')

        data_header_readed = False #si le header de la section [Data] a ete lu

        #on copie les lignes du sample sheet vers le sample sheet concatene
        for line in open(sample_sheet_path):

            # si le sample sheet concatene est nouvellement cree, on copy egalement le header du sample sheet
            if not concat_sample_sheet_exist:
                if re.search('Experiment Name', line):
                    concat_file_handler.write('Experiment Name,' + concat_sample_sheet_name + '\n')
                else:
                    line = re.sub(r',2,',',pulsenet,',line) # car le projet 2 correspond au projet salmonella pulse-net
                    concat_file_handler.write(line)
            # sinon on y copy uniquement les lignes correspondant aux samples
            elif re.search('Sample_ID', line):
                data_header_readed = True

            elif data_header_readed:
                line = re.sub(r',2,', ',pulsenet,', line) # car le projet 2 correspond au projet salmonella pulse-net
                concat_file_handler.write(line)

        concat_file_handler.write('\n')
        concat_file_handler.close()

    def SetNewRunName(self):
        '''
        On defini le nom de la run a partir de la quatrieme ligne du SampleSheet.csv
        :return:
        '''
        self.new_run_name = ""
        self.cartridge_name = ""

        SampleSheetHandler = open(self.MiSeqRunObj.GetSampleSheetPath())

        for line in SampleSheetHandler:
            # print line
            if re.search(r'Experiment Name', line):
                self.new_run_name = line.split(',')
                self.new_run_name = self.new_run_name[1].strip()

        search_obj = re.search(r'^(\S+_\S+)_(\S+)$',self.new_run_name)

        if search_obj:
            self.new_run_name = search_obj.group(1)
            self.cartridge_name = search_obj.group(2)
        else:
            self.ftl.LogMessage("Nom de run inexistant")

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
                self.LspqMiSeqRunObj = RunOnPartageLspqMiSeq(self.new_run_name,self.path_setter.GetPartageLspqMiSeqRootDir(),self.cartridge_name)

                #Arborescence du repertoire d analyse a cree sur le S:\\Partage\LSPQ_MiSeq\
                self.LspqMiSeqRunObj.SetPath()

                self.ftl.LogMessage("Creation de l'arborescence de la run {new_runname} dans S:\Partage\LSPQ_MiSeq".format(new_runname = self.LspqMiSeqRunObj.GetRunName()))

                # On cree l arborescence du repertoire d analyse sur S:\\Partage\LSPQ_MiSeq\
                self.LspqMiSeqRunObj.CreatePath()

                self.ftl.LogMessage("Export des fichiers du MiSeq run {0} vers {1} en cours".format(runname,self.LspqMiSeqRunObj.GetRunPath()))

                #Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\1_Experimental
                self.ExportToLspqMiSeqExperimental()

                if self.CheckIfIridaSamplesInRun():
                    self.CreateIridaSampleSheet()
                else:
                    self.ImportIridaUploaderInfoFile()

                #Concatener les sample sheet
                self.ConcatSampleSheet()

                self.ExportToLspqMiSeqMiSeqRunTrace()

                #Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\3_SequencesBrutes
                self.ExportToLspqMiSeqSequenceBrute()

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
        self.irida_samples_in_run = False

    def GetRunPath(self):
        return  self.runpath

    def CreateIridaSampleSheet(self):
        """
        Creer une sample sheet contenant seulement les samples a transferer sur irida
        :return:
        """

        shutil.move(self.sampleSheet_file_path,os.path.join(self.runpath,'SampleSheet_original.csv'))

        with open(self.sampleSheet_file_path,'w') as sheet:
            with open(os.path.join(self.runpath,'SampleSheet_original.csv')) as sheet_ori:
                sample_header_read = False
                for line in sheet_ori:
                    if re.search(r'Sample_ID', line):
                        sample_header_read = True

                    if not sample_header_read:
                        sheet.write(line)

                    elif re.search(r'Sample_ID',line):
                        sheet.write(line)

                    else:
                        if re.search(r'^.*,.*,.*,.*,.*,.*,.*,.*,2,',line):
                            sheet.write(line)

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

    def __init__(self,RunName,basedir,CartridgeName):

        #Nom de la run
        self.runname = RunName

        #Nom de la cartouche
        self.cartridgename = CartridgeName

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
        self.miseq_run_trace = os.path.join(self.runpath,'2_MiSeqRunTrace')
        self.miseq_run_trace_cartridge = os.path.join(self.miseq_run_trace,self.cartridgename)
        self.sequences_brutes_path = os.path.join(self.runpath,'3_SequencesBrutes')
        self.analyse_path = os.path.join(self.runpath,'4_Analyse')

    def CreatePath(self):
        '''
        Setting des paths de la nouvelle run sur S:\\Partage\LSPQ_MiSeq\
        :return:
        '''

        #Creation du repertoire racine
        if os.path.isdir(self.runpath):
            pass
        else:
            os.makedirs(self.runpath)

        #Creation du sous repertoire 1_Experimental
        if os.path.isdir(self.experimental_path):
            pass
        else:
            os.makedirs(self.experimental_path)

        #Creation du sous repertoire 2_MiSeqRunTrace
        if os.path.isdir(self.miseq_run_trace):
            pass
            os.makedirs(self.miseq_run_trace_cartridge)
        else:
            os.makedirs(self.miseq_run_trace)
            os.makedirs(self.miseq_run_trace_cartridge)

        #Creation du sous repertoire 3_SequencesBrutes
        if os.path.isdir(self.sequences_brutes_path):
            pass
        else:
            os.makedirs(self.sequences_brutes_path)

        #Creation du sous repertoire 4_Analyse
        if os.path.isdir(self.analyse_path):
            pass
        else:
            os.makedirs(self.analyse_path)
            #Creation des sous repertoires de project dans 4_Analyse
            self.CreateProjectSubDir()

    #Getter des path
    def GetExpPath(self):
        return self.experimental_path

    def GetMiseqRunTrace(self):
        return self.miseq_run_trace

    def GetMiseqRunTraceCartridge(self):
        return self.miseq_run_trace_cartridge

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
        self.SampleSheetName = self.runname + '_' + self.cartridgename +".csv"

if __name__ == '__main__':
    w = Watcher()
    w.run()



