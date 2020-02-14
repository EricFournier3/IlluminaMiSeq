# coding=utf-8

import threading
import time
import os
import csv
import re
from EmailSender import IridaTransferStatusEmailer
from ParameterHandler import ThreadManager

class IridaTransferMonitorer():
    def __init__(self,monitored_file,debug_level,runid,lspq_miseq_run_name):
        pass
        self.monitored_file_std = monitored_file['standard']
        self.monitored_file_mt = monitored_file['multithread']
        self.wait_message = "En attente du transfert vers Irida ...\n"
        self.end_message = "Fin du transfert Irida-pulsenet\n"
        self.debug_level = debug_level
        self.miseq_runid = runid
        self.lspq_miseq_run_name = lspq_miseq_run_name
        self.irida_transfer_status_emailer = IridaTransferStatusEmailer(self.miseq_runid,self.lspq_miseq_run_name,self.debug_level)

        self.thread_manager = ThreadManager(debug_level=self.debug_level)
        self.thread_manager.OpenParamFile()
        self.thread_manager.ParseParamFile()
        self.thread_manager.CloseParamFile()


    def MonitorTransfer(self,thread_name):
        pass
        #on envoie pas le email tant que le fichier  monitored_file n existe pas ou que son statut n est pas a done

        i = 0
        print self.wait_message
        while not(self.CheckIfStandardMonitoredFileExist()) or not(self.CheckStandardMonitoredFileStatus()):

            time.sleep(self.thread_manager.GetSleepTime())

        print self.end_message
        self.irida_transfer_status_emailer.SendIridaTransferStatusByEmail()

    def StartMonitoring(self):
        thread = threading.Thread(target=self.MonitorTransfer,args=("Irida_transfer_monitorer",))
        thread.start()

    def CheckIfStandardMonitoredFileExist(self):
        return os.path.exists(self.monitored_file_std)

    def CheckIfMultithreadMonitoredFileExist(self):
        return os.path.exists(self.monitored_file_mt)

    def CheckMultithreadMonitoredFileStatus(self):
        pass
        status = ""
        with open(self.monitored_file_mt, 'r') as file:
            for row in file:
                if re.search(r'Upload Status', row):
                    status = row.split(':')[1].strip(' ').replace('"', '', 2)

        if status.upper() == "COMPLETE":
            return True
        else:
            return False

    def CheckStandardMonitoredFileStatus(self):
        pass
        status = ""
        with open(self.monitored_file_std, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                status = (str(row[0]).split(':'))[1].strip(' ').replace('"', '', 2)

        if status.upper() == "COMPLETE":
            return True
        else:
            return False