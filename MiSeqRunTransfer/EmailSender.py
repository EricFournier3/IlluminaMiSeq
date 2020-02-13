# encoding: iso-8859-15

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ParameterHandler import EmailDestManager

from ParameterHandler import EmailDestManager

class IridaTransferStatusEmailer():
    def __init__(self):
        pass


class IridaSpecEmailer():
    def __init__(self,files_to_send,debug_lev,lspq_miseq_dir_name, miseq_run_id):
        self.lspq_miseq_dir_name = lspq_miseq_dir_name
        self.miseq_run_id = miseq_run_id
        self.files_to_send = files_to_send
        self.good_file = self.files_to_send['good']
        self.bad_file = self.files_to_send['bad']
        self.debug_lev = debug_lev

        self.server_host = 'smtp.inspq.qc.ca:25'

        self.message_from = "eric.fournier@inspq.qc.ca"
        self.email_manager = EmailDestManager(send_type='irida', debug_level=self.debug_lev)
        self.email_manager.OpenParamFile()
        self.email_manager.ParseParamFile()
        self.email_manager.CloseParamFile()


        self.message_to = self.email_manager.GetRecipientList()

        self.message_text = "Bonjour,\nci-joint la liste de spécimens pulsenet/ngs acceptés et rejetés"
        self.message_subject = "Triage spécimens pulsenet-ngs: {0}:{1}".format(self.miseq_run_id,self.lspq_miseq_dir_name)

    def OpenParamFile(self):
        self.email_manager.OpenParamFile()

    def ParseParamFile(self):
        self.email_manager.ParseParamFile()

    def SendGoodAndBadSpecListByEmail(self):

        msg_obj = MIMEMultipart()
        msg_obj.attach(MIMEText(self.message_text,_charset='iso-8859-15'))
        msg_obj['Subject'] = self.message_subject

        msg_obj['From'] = "eric.fournier@inspq.qc.ca"
        msg_obj['To'] = ';'.join(self.message_to)

        for file_to_send in dict(self.files_to_send).values():
            with open(file_to_send,'rb') as f:
                part = MIMEApplication(f.read(),Name=basename(f.name))
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f.name)
                msg_obj.attach(part)

        server = smtplib.SMTP(self.server_host)
        server.sendmail(msg_obj['From'], self.message_to, msg_obj.as_string())
        server.quit()