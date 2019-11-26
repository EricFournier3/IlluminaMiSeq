import yaml
import os

yaml.warnings({'YAMLLoadWarning': False})

"""
Eric Fournier 2019-07-31
"""

#Pour debug
debug_setting = {1: 'debug_inspq_6499', 2: 'debug_miseq', 3: 'no_debug'}

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

        if(self.debug_val == 'debug_inspq_6499'):
            self.param_file = os.path.join('U:\\', 'TEMP', 'LSPQ_MiSeq', 'MiSeqRunTransferParam.yaml')
        else:
            self.param_file = os.path.join('C:\\','ScriptParameterFiles','MiSeqRunTransferParam.yaml')

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

        #les path de la run dans S:\Partage\LSPQ_MiSeq
        self.partage_lspq_miseq_root_dir = self.all_dict['runs_on_partage_lspq_miseq'][0][self.debug_val]

        self.irida_uploader_info = self.all_dict['irida_uploader_info'][0][self.debug_val]

    #Les getter
    def GetLogginFile(self):
        return self.loggin_file

    def GetMiSeqRootDir(self):
        return  self.miseq_root_dir

    def GetPartageLspqMiSeqRootDir(self):
        return self.partage_lspq_miseq_root_dir

    def GetIridaUploaderInfoFile(self):
        return  self.irida_uploader_info

