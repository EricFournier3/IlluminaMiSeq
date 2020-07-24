# coding=utf-8
import time
import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import Logger
import ParameterHandler
import re
from EmailSender import *
from Stat import MiSeqStatComputer

"""
Eric Fournier 2019-07-30
Script de transfert automatique des runs MiSeq terminées vers S:\\Partage\LSPQ_MiSeq

Procedure pour compiler avec pyinstaller:
    1- Copier les scripts CheckFinishedMiSeqRun.py, Logger.py et ParameterHandler.py Deamons.py EmailSender.py Tools.py dans C:\Users\foueri01\Documents\PyinstallerCompilation
    2- aller dans C:\Users\foueri01\Documents\PyinstallerCompilation avec une console ligne de commande 
    3- Executer la commande suivante
            pyinstaller.exe --onefile --icon=watchdog.ico CheckFinishedMiSeqRun.py
    4- L executable CheckFinishedMiSeqRun.exe sera dans C:\Users\foueri01\Documents\PyinstallerCompilation\Dist
    5-  Pour voir l executable avec le nouvel icone, il faut le copier dans un autre repertoire
    6- S assurer de la bonne version du MiSeqRunTransferParam dans C:\WatchDogFiles sur INSPQ-7041
            
"""

"""
Liste des modifications

- Modif_20200130 : 2020-01-30 Eric Fournier 
        > Backup de la run MiSeq
        > Les runs sur LSPQ_MiSeq sont maintenant classees par annee
        
- Modif_20200211: 2020-02-11 Eric Fournier
    > Quelques ajustements pour la creation de la sample sheet irida
    > Creation Manuel du fichier .miseqUploaderInfo
    > Ne plus copier automatiquement les SampleSheet de cassette dans LSPQ_MiSeq
    > Ne plus tenter d envoyer sur Irida les fastq trop petit => creer fichier SamplesTransfered et SampleNotTransfered et envoie par email
    > email lorsque transfert Irida termine
    
- Modif_20200214: Eric Fournier 2020-02-14
    > Appeler le IridaUploader
    
- Modif_20200306 Eric Fournier 2020-03-06
    > Choisir d executer ou non le irida uploader
    > Calcul des statistique MiSeq

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
        #print('DIRECTORY_TO_WATCH ', self.DIRECTORY_TO_WATCH)

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
        #Modif_20200211
        if not os.path.exists(os.path.join(self.LspqMiSeqRunObj.GetExpPath(),self.LspqMiSeqRunObj.GetNewSampleSheetName())):
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

    def BuildGoodAndBadFastqList(self,min_fastq_size):
        #Modif_20200211
        pass
        #liste specimen ok => on enregistre dans fichier
        #liste specime non ok => on enregistre
        #envoye par email a sadjia

        good_spec_list = []
        bad_spec_list = []

        for fastq in os.listdir(self.MiSeqRunObj.GetBaseCallPath()):
            if (str(fastq).endswith('.fastq.gz')):

                spec_name = fastq.split('_')[0]
                if(os.stat(os.path.join(self.MiSeqRunObj.GetBaseCallPath(),fastq)).st_size > min_fastq_size):

                    good_spec_list.append(spec_name)
                else:
                    bad_spec_list.append(spec_name)

        good_spec_set = set(good_spec_list)
        bad_spec_set = set(bad_spec_list)

        good_spec_list = list(good_spec_set - bad_spec_set)
        bad_spec_list = list(bad_spec_set)

        spec_dir = {'good':good_spec_list, 'bad':bad_spec_list}

        return spec_dir



    def BackupMiSeqRun(self):
        '''
        Modif_20200130

        Sauvegarde de la run MiSeq

        :return:
        '''

        self.RunBackuperObj.LauchRunBackup()

    def ExportToLspqMiSeqAnalyse(self):
        '''
        Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\4_Analyse

        :return:
        '''
        pass

    def CreateIridaSampleSheet(self,file_size_manager,run_name):
        """
        On cree dans le repertoire racine de la run sur le MiSeq, un
        SampleSheet.csv qui contient seulement des specimens irida
        :return:
        """

        # APPELE UNE FONCTION QUI S ASSURE QUE LA R1 > file_size_manager.GetMinFastqSize() ET QUE LA R2 > file_size_manager.GetMinFastqSize()
        # Modif_20200211
        good_and_bad_spec_dir = self.BuildGoodAndBadFastqList(file_size_manager.GetMinFastqSize())

        self.MiSeqRunObj.CreateIridaSampleSheet(good_and_bad_spec_dir,run_name)

    def CheckIfIridaSamplesInRun(self,sample_sheet):
        header_readed = False

        with open(sample_sheet) as ss:
            for line in ss:
                if(re.search('Sample_ID',line)):
                    header_readed = True
                    continue
                elif header_readed:
                    line_list = str(line).split(',')
                    #print 'line_list ', line_list
                    if(str(line_list[8]) == '2'):
                        return True

        return False

    def ImportIridaUploaderInfoFile(self):
        """
        Fichier .miseqUploaderInfo avec status a Complete pour ne pas que le irida scan cette run
        :return:
        """

        #shutil.copy(self.path_setter.GetIridaUploaderInfoFile(),self.MiSeqRunObj.GetRunPath())

        #Modif_20200211
        with open(os.path.join(self.MiSeqRunObj.GetRunPath(),".miseqUploaderInfo"),'w') as irida_status_f:
            irida_status_f.write(r'{"Upload Status": "Complete", "Upload ID": "99"}')

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
            if((event.src_path.endswith('CompletedJobInfo.xml')) and (not os.path.dirname(event.src_path).endswith('Alignment'))):
                # Parameters handler
                self.path_setter = ParameterHandler.PathSetter(my_debug_level)
                self.path_setter.OpenParamFile()
                self.path_setter.ParseParamFile()

                #Modif_20200211
                self.file_size_manager = ParameterHandler.FileSizeManager(my_debug_level)
                self.file_size_manager.OpenParamFile()
                self.file_size_manager.ParseParamFile()

                #path vers la run sur le MiSeq
                runpath = os.path.dirname(event.src_path)

                #Id de la run
                runname = os.path.basename(runpath)

                #Un object structure de la run terminee sur le MiSeq
                self.MiSeqRunObj = RunOnMiSeq(runpath)

                #Modif_20200130
                #Object permettant la copie de run sur le disque 8T
                self.RunBackuperObj = RunBackuper(runpath,self.path_setter.GetBackupDiskDir())

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

                if self.CheckIfIridaSamplesInRun(self.MiSeqRunObj.GetSampleSheetPath()):

                    self.CreateIridaSampleSheet(self.file_size_manager,self.new_run_name)
                    #self.MiSeqRunObj.MonitorIridaSamplesTransfer(self.new_run_name)
                    self.MiSeqRunObj.LaunchIridaUploader(self.new_run_name)
                else:
                    self.ImportIridaUploaderInfoFile()

                #Concatener les sample sheet
                self.ConcatSampleSheet()

                self.ExportToLspqMiSeqMiSeqRunTrace()

                #Export des fichiers vers S:\\Partage\LSPQ_MiSeq\RunName\3_SequencesBrutes
                #Modif_20200211
                self.ExportToLspqMiSeqSequenceBrute()

                #Modif_20200306
                self.ftl.LogMessage("Calcul des statistiques pour {0}".format(runname))
                self.MiSeqRunObj.ComputeQualStat(self.LspqMiSeqRunObj.GetRunPath())

                self.ftl.LogMessage("Export des fichiers du MiSeq run {0} vers {1} est termine".format(runname, self.LspqMiSeqRunObj.GetRunPath()))

                # Modif_20200130
                self.ftl.LogMessage("Debut Backup run {0}".format(runname))
                self.BackupMiSeqRun()
                self.ftl.LogMessage("Fin Backup run {0}\n ----------------------------------".format(runname))

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

    def ComputeQualStat(self,lspq_miseq_dir_path):
        '''
        Calculs de statistique des qualité
        :return:
        '''
        self.stat_computer = MiSeqStatComputer(self.runpath,lspq_miseq_dir_path)
        self.stat_computer.ComputeRunStat()

        self.stat_computer.ComputeSamplesStat()

        self.stat_computer.WriteStat()

    def CreateIridaSampleSheet(self,good_and_bad_spec_dir,lspq_miseq_dir_name):
        """
        Creer une sample sheet contenant seulement les samples a transferer sur irida
        :return:
        """

        shutil.move(self.sampleSheet_file_path,os.path.join(self.runpath,'SampleSheet_original.csv'))

        good_irida_specs = []
        bad_irida_specs = []

        #Modif_20200211
        with open(os.path.join(self.runpath,'SampleSheet_original.csv')) as sheet_ori:
            data = sheet_ori.read().rstrip('\n')

        # Modif_20200211
        with open(os.path.join(self.runpath,'SampleSheet_temp.csv'),'w') as sheet_temp:
            sheet_temp.write(data)

        with open(self.sampleSheet_file_path,'w') as sheet:
            #Modif_20200211
            with open(os.path.join(self.runpath,'SampleSheet_temp.csv')) as sheet_ori:
                sample_header_read = False
                for line in sheet_ori:
                    if re.search(r'Sample_ID', line):
                        sample_header_read = True

                    if not sample_header_read:
                        sheet.write(line)

                    elif re.search(r'Sample_ID',line):
                        #Modif_20200211
                        line_list = line.split(',')
                        line_list[0] = 'Sample_ID'
                        line_list[1] = 'Sample_Name'
                        line = ','.join(line_list)
                        sheet.write(line)

                    else:
                        if re.search(r'^.*,.*,.*,.*,.*,.*,.*,.*,2,',line):
                            line_list = line.split(',')
                            line_list[1] = line_list[0]
                            line = ','.join(line_list)
                            if line_list[0] in good_and_bad_spec_dir['good']:
                                sheet.write(line)
                                good_irida_specs.append(line_list[0])
                            elif line_list[0] in good_and_bad_spec_dir['bad']:
                                bad_irida_specs.append(line_list[0])

            good_and_bad_iridaspec_dir = {'good':good_irida_specs, 'bad':bad_irida_specs }

            good_file_name = 'GoodIridaSamples_{0}_{1}.csv'.format(os.path.basename(self.runpath),lspq_miseq_dir_name)
            bad_file_name = 'BadIridaSamples_{0}_{1}.csv'.format(os.path.basename(self.runpath), lspq_miseq_dir_name)

        self.WriteGoodAndBadIridaSpecFile(good_and_bad_iridaspec_dir,good_file_name,bad_file_name)
        self.EmailGoodAndBadIridaSpecFile(os.path.join(self.runpath,good_file_name),os.path.join(self.runpath,bad_file_name),lspq_miseq_dir_name)

    def LaunchIridaUploader(self,lspq_miseq_run_name):
        #TODO verfier et activer le check point => besoin d un client checkpoint
        from Deamons import IridaUploader
        irida_uploader_obj = IridaUploader(self.runpath,lspq_miseq_run_name,my_debug_level)

        #Modif_20200306
        if irida_uploader_obj.mode == "ON":
            irida_uploader_obj.Init()
        else:
            irida_uploader_obj.irida_tranfer_status_logger.LogMessage("Irida uploader is disabled")

    def WriteGoodAndBadIridaSpecFile(self,good_and_bad_iridaspec_dir,good_file_name,bad_file_name):

        """
        Modif_20200211
        Creer les fichiers liste des specimens pulsenet a transferer et a ne pas transferer sur irida

        :param spec_dir:
        :return:
        """
        out_good = open(os.path.join(self.runpath,good_file_name),'w')
        out_bad = open(os.path.join(self.runpath,bad_file_name),'w')

        for good_spec in good_and_bad_iridaspec_dir['good']:
            out_good.write(good_spec + '\n')

        for bad_spec in good_and_bad_iridaspec_dir['bad']:
            out_bad.write(bad_spec + '\n')

        out_bad.close()
        out_good.close()

    def EmailGoodAndBadIridaSpecFile(self,good_file,bad_file,lspq_miseq_dir_name):
        """
        Modif_20200211
        Envoyer par email les fichiers liste des specimens pulsenet a transferer et a ne pas transferer sur irida
        :return:
        """

        files_to_send = {'good':good_file,'bad':bad_file}
        irida_spec_emailer = IridaSpecEmailer(files_to_send,my_debug_level,lspq_miseq_dir_name,os.path.basename(self.runpath))
        irida_spec_emailer.SendGoodAndBadSpecListByEmail()



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

    def MonitorIridaSamplesTransfer(self,lspq_miseq_dir_name):
        from Deamons import IridaTransferMonitorer
        #ICI
        monitored_file_standard = os.path.join(self.runpath,".miseqUploaderInfo")
        monitored_file_multithread = os.path.join(self.runpath, "irida_uploader_status.info")
        monitorer = IridaTransferMonitorer({'standard':monitored_file_standard,'multithread':monitored_file_multithread},my_debug_level,self.runpath,lspq_miseq_dir_name)
        monitorer.StartMonitoring()


class RunBackuper():
    """
    Modif_20200130
    Pour le backup des runs sur le disque 8T
    """
    def __init__(self,run_path,backup_disk_path):
        pass
        self.runPath = run_path
        self.BackupDiskPath = backup_disk_path

    def LauchRunBackup(self):
        src = re.sub('MiSeqOutput','MiSeqAnalysis',self.runPath)
        dest = os.path.join(self.BackupDiskPath,os.path.basename(self.runPath))
        shutil.copytree(src, dest)

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
        #Modif_20200130 ajout de l annee
        self.runpath = os.path.join(self.basedir,self.runname[0:4],self.runname)


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



