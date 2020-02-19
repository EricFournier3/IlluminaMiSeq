# coding=utf-8

import threading
import time
import os
import csv
import re
from EmailSender import IridaTransferStatusEmailer
from ParameterHandler import ThreadManager,IridaUploaderManager
import subprocess


class IridaUploader():
    def __init__(self, run_path, lspq_miseq_run_name,debug_level):
        self.run_path = run_path
        self.lspq_miseq_run_name = lspq_miseq_run_name
        self.debug_level = debug_level
        self.exec_name = 'iridauploader'
        self.parser = 'miseq'

        self.thread_manager = ThreadManager(debug_level=self.debug_level)
        self.thread_manager.OpenParamFile()
        self.thread_manager.ParseParamFile()
        self.thread_manager.CloseParamFile()

        self.parameter_manager = IridaUploaderManager(self.debug_level)
        self.parameter_manager.OpenParamFile()
        self.parameter_manager.ParseParamFile()
        self.parameter_manager.CloseParamFile()

        self.log_file = os.path.join(self.run_path,"IridaUploaderLogFromWatchDog.log")

        self.status_file = os.path.join(self.run_path,"irida_uploader_status.info")

        self.thread_number = self.parameter_manager.GetThreadNumber()

        self.status_emailer = IridaTransferStatusEmailer(os.path.basename(run_path),self.lspq_miseq_run_name,self.debug_level)

        self.is_error = False

    def Go(self,thread_name):
        #TODO LOGGER DANS DES FICHIERS
        while not self.CheckStatusOk():
            print "Check"
            time.sleep(self.thread_manager.GetSleepTime())

            if(self.is_error):
                #TODO Connect Check Point
                print "Try to reconnect"
                log_handler = open(self.log_file, 'a')
                #process = subprocess.Popen([self.exec_name,-m,'-t',str(self.thread_number),'-d',self.run_path,'-cr',self.parser],stdout=log_handler,stderr=log_handler,shell=True)
                process = subprocess.Popen([self.exec_name, '-d', self.run_path, '-cr', self.parser],stdout=log_handler, stderr=log_handler, shell=True)
                process.communicate()
                process.terminate()
                log_handler.close()
        #
        # log_handler.close()
        #
        # if self.CheckIfTransferOk():
        #    self.SendTransferStatusEmail()
        # else:
        #    print "Erreur de transfert Irida" #TODO logger en console avec logger



        print "FINISH **********"
            

    def CheckStatusOk(self):

        self.is_error = False

        if not os.path.exists(self.status_file):
            return False


        status = ""
        with open(self.status_file, 'r') as file:
            for row in file:
                if re.search(r'Upload Status', row):
                    status = row.split(':')[1]
                    status = status.rstrip()
                    status = status.lstrip()
                    status = status.replace('"', '', 2)

        print "Status is ",status

        if status.upper() == "COMPLETE":

            return True
        else:
            if(re.search('error',status)):
                os.remove(self.status_file)
                self.is_error = True
            return False

    def CheckIfTransferOk(self):
        log_handler = open(self.log_file)

        for line in log_handler:
            if re.search('ERROR',line):
                log_handler.close()
                return False

        log_handler.close()
        return True


    def Init(self):
        thread = threading.Thread(target=self.Go, args=("IridaUploader",))
        thread.start()

        log_handler = open(self.log_file, 'a')
        #TODO DEMARRER LE EndPoint
        print "Start i"
        process = subprocess.Popen([self.exec_name, '-t', str(self.thread_number), '-d', self.run_path, '-cr', self.parser],stdout=log_handler, stderr=log_handler, shell=True)
        process.communicate()
        process.terminate()
        print "ENd 1"
        log_handler.close()



    def SendTransferStatusEmail(self):
        self.status_emailer.SendIridaTransferStatusByEmail()

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