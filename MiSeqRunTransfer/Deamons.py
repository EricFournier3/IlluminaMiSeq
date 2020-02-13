# coding=utf-8

import threading
import time
import os
import csv

class IridaTransferMonitorer():
    def __init__(self,monitored_file):
        pass
        self.monitored_file = monitored_file
        self.wait_message = "En attente du transfert vers Irida ...\n"


    def MonitorTransfer(self,thread_name):
        pass
        #on envoie pas le email tant que le fichier  monitored_file n existe pas ou que son statut n est pas a done

        i = 0

        while not(self.CheckIfMonitoredFileExist()) or not(self.CheckMonitoredFileStatus()):
        #while(i<10):
            print self.wait_message
            time.sleep(2)
            #time.sleep(300)


        print "On peut envoyer le email"

    def StartMonitoring(self):
        thread = threading.Thread(target=self.MonitorTransfer,args=("Irida_transfer_monitorer",))
        thread.start()

    def CheckIfMonitoredFileExist(self):
        pass
        return os.path.exists(self.monitored_file)

    def CheckMonitoredFileStatus(self):
        pass
        status = ""
        with open(self.monitored_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                status = (str(row[0]).split(':'))[1].strip('" ')

        if status == "Complete":
            return True
        else:
            return False