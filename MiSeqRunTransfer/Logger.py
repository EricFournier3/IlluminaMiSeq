import logging
import os

"""
Eric Fournier 2019-07-31
"""

#Pour debug
debug_setting = {1: 'debug_inspq_6499', 2: 'debug_MiSeq', 3: 'none'}

class FileTransferLogger:
    """
    Pour Loggin des transferts de fichiers des runs MiSeq terminees vers S:\\Partage\LSPQ_MiSeq
    """
    def __init__(self,logger_name,debug_level):

        #niveau de debuggage
        self.debug_val = debug_setting[debug_level]

        #niveau de login
        self.log_level = logging.INFO

        #nom du logger
        self.logger_name = logger_name + '_Logger'

        #pour les path vers le FinishedRunLog.log
        self.output = ""

        #le logger
        self.logger = None

        #pour le format du message affiche
        self.formatter = None

        #pour affichage dans la console
        self.console_handler = None

        #pour affichage dans FinishedRunLog.log
        self.file_handler = None

        #pour definir le FinishedRunLog.log
        self.SetOutput()

        #Setting du logger, formatter et handlers
        self.Configure()

    def LogMessage(self,message):
        """
        Affichage du message
        :param message:
        :return:
        """
        self.logger.info(message)

    def SetLogger(self):
        """
        Creation du logger
        :return:
        """
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.INFO)

    def SetFormatter(self):
        """
        Creation du formatter
        :return:
        """
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%m/%d/%Y %I:%M:%S')

    def SetFileHandler(self):
        """
        Setting du file handler
        :return:
        """
        self.file_handler = logging.FileHandler(self.output)
        self.file_handler.setLevel(self.log_level)
        self.file_handler.setFormatter(self.formatter)

    def SetConsoleHandler(self):
        """
        Setting du console handler
        :return:
        """
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(self.log_level)
        self.console_handler.setFormatter(self.formatter)

    def AddHandlerToLogger(self):
        """
        Ajout des handler au logger
        :return:
        """
        self.logger.addHandler(self.console_handler)
        self.logger.addHandler(self.file_handler)

    def Configure(self):
        """
        Setting du handler, formatter et des handler
        :return:
        """
        self.SetLogger()
        self.SetFormatter()
        self.SetConsoleHandler()
        self.SetFileHandler()
        self.AddHandlerToLogger()

    def SetOutput(self):
        """
        Path du FinishedRunLog.log selon le niveau de debuggage
        :return:
        """
        if (self.debug_val == 'debug_inspq_6499'):
            self.output = os.path.join('U:', 'TEMP', 'LSPQ_MiSeq', 'FinishedRunLog.log')
        elif (self.debug_val == 'debug_MiSeq'):
            self.output = os.path.join('\\swsfi52p', 'Secure_stemarie', 'Partage', 'LSPQ_MiSeq', 'TEMP_TEST','FinishedRunLog.log')
        else:
            self.output = os.path.join('\\swsfi52p', 'Secure_stemarie', 'Partage', 'LSPQ_MiSeq', 'FinishedRunLog.log')