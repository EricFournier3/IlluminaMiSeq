import yaml
import os

yaml.warnings({'YAMLLoadWarning': False})

"""
Eric Fournier 2019-07-31
"""

debug_setting = {1: 'debug_inspq_6499_I', 2: 'debug_inspq_6499_J', 3: 'no_debug_inspq_8719', 4: 'no_debug_inspq_8900'}


class ThreadManager():
    def __init__(self,debug_level):
        self.debug_val = debug_setting[debug_level]
        self.param_file = os.path.join('C:\\', 'WatchDogFiles', 'MiSeqRunTransferParam.yaml')

    def OpenParamFile(self):
        """
        Ouverture du fichier de parametres
        :return:
        """
        self.param_file_handle = open(self.param_file)

    def CloseParamFile(self):
        """
        Fermeture du fichier de parametres
        :return:
        """
        self.param_file_handle.close()

    def ParseParamFile(self):
        self.all_dict = yaml.load(self.param_file_handle)

        self.sleep_time = int(self.all_dict['thread_sleep'][0][self.debug_val])

    def GetSleepTime(self):
        return self.sleep_time


class FileSizeManager():
    """
    #Modif_20200211
    Lecteur de taille de fichiers

    """

    def __init__(self,debug_level):
        self.debug_val = debug_setting[debug_level]
        self.param_file = os.path.join('C:\\', 'WatchDogFiles', 'MiSeqRunTransferParam.yaml')

    def OpenParamFile(self):
        """
        Ouverture du fichier de parametres
        :return:
        """
        self.param_file_handle = open(self.param_file)

    def CloseParamFile(self):
        """
        Fermeture du fichier de parametres
        :return:
        """
        self.param_file_handle.close()

    def ParseParamFile(self):
        self.all_dict = yaml.load(self.param_file_handle)

        self.min_fastq_size = self.all_dict['min_fastq_size'][0][self.debug_val]

    def GetMinFastqSize(self):
        return self.min_fastq_size


class EmailDestManager():
    """
    Modif_20200211

    """

    send_type_dict = {'irida': 'irida_email_recipient'}

    def __init__(self,debug_level,send_type):
        self.debug_val = debug_setting[debug_level]
        self.param_file = os.path.join('C:\\', 'WatchDogFiles', 'MiSeqRunTransferParam.yaml')
        self.send_type = send_type

    def OpenParamFile(self):
        """
        Ouverture du fichier de parametres
        :return:
        """
        self.param_file_handle = open(self.param_file)

    def CloseParamFile(self):
        """
        Fermeture du fichier de parametres
        :return:
        """
        self.param_file_handle.close()

    def ParseParamFile(self):
        self.all_dict = yaml.load(self.param_file_handle)

        self.recipient_list = self.all_dict[EmailDestManager.send_type_dict[self.send_type]][0][self.debug_val]


    def GetRecipientList(self):

        return self.recipient_list


class PathSetter():
    """
    Gere les chemins d acces definis dans le fichier de parametres MiSeqRunTransferParam.yaml

    """
    def __init__(self,debug_level):
        #le niveau de debuggage
        self.debug_val = debug_setting[debug_level]

        #le fichier de parametre
        self.param_file = None
        self.param_file_handle = None

        #les parametres
        self.all_dict = None

        #pour les path du fichier de loggin
        self.loggin_file = None

        #pour les path de la run sur le MiSeq
        self.miseq_root_dir = None

        #pour les path de la run dans S:\Partage\LSPQ_MiSeq
        self.partage_lspq_miseq_root_dir = None

        self.param_file = os.path.join('C:\\', 'WatchDogFiles', 'MiSeqRunTransferParam.yaml')


    def OpenParamFile(self):
        """
        Ouverture du fichier de parametres
        :return:
        """
        self.param_file_handle = open(self.param_file)

    def CloseParamFile(self):
        """
        Fermeture du fichier de parametres
        :return:
        """
        self.param_file_handle.close()

    def ParseParamFile(self):
        """
        Parsing du fichier de parametre
        :return:
        """

        #tous les parametres
        self.all_dict = yaml.load(self.param_file_handle)

        #le path du fichier de loggin

        self.loggin_file = self.all_dict['loggin'][0][self.debug_val]

        #les path de la run sur le MiSeq
        self.miseq_root_dir = self.all_dict['runs_on_miseq'][0][self.debug_val]

        #print " miseq_root_dir " + self.miseq_root_dir

        #les path de la run dans S:\Partage\LSPQ_MiSeq
        self.partage_lspq_miseq_root_dir = self.all_dict['runs_on_partage_lspq_miseq'][0][self.debug_val]

        #path vers le .miseqUploaderInfo
        self.irida_uploader_info = self.all_dict['irida_uploader_info'][0][self.debug_val]

        #Modif_20200130
        #path vers le disque 8T de sauvegarde des runs
        self.backup_disk_dir = self.all_dict['backup_disk'][0][self.debug_val]



    #Les getter
    def GetLogginFile(self):
        return self.loggin_file

    def GetMiSeqRootDir(self):
        return  self.miseq_root_dir

    def GetPartageLspqMiSeqRootDir(self):
        return self.partage_lspq_miseq_root_dir

    def GetIridaUploaderInfoFile(self):
        return  self.irida_uploader_info

    def GetBackupDiskDir(self):
        """
        Modif_20200130
        :return:
        """
        return self.backup_disk_dir


