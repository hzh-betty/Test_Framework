import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from conf.operator_config import OperatorConfig
from common.record_log import logs
import os

conf = OperatorConfig()


class SendEmail:
    """Base email class: build content and send with optional attachment"""

    def __init__(self,
                 host=conf.get_section_for_data('EMAIL', 'host'),
                 user=conf.get_section_for_data('EMAIL', 'user'),
                 passwd=conf.get_section_for_data('EMAIL', 'passwd')):
        self.__host = host
        self.__user = user
        self.__passwd = passwd

    def build_content(self, subject, email_content, addressee=None, atta_file=None):
        """
        Build and send email
        :param subject:  subject
        :param email_content: email body
        :param addressee: recipients (semicolon-separated)
        :param atta_file: attachment path
        """
        sender = f"Liaison Officer <{self.__user}>"

        # recipients list
        if addressee is None:
            addressee = conf.get_section_for_data('EMAIL', 'addressee').split(';')
        else:
            addressee = addressee.split(';')

        # create email object
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = ', '.join(addressee)
        message['Subject'] = Header(subject, 'utf-8')

        # add body
        message.attach(MIMEText(email_content, 'plain', 'utf-8'))

        # add attachment if exists
        if atta_file and os.path.isfile(atta_file):
            with open(atta_file, 'rb') as f:
                atta = MIMEApplication(f.read())
            filename = os.path.basename(atta_file)
            atta.add_header('Content-Disposition', 'attachment', filename=Header(filename, 'utf-8').encode())
            message.attach(atta)

        # send email
        try:
            with smtplib.SMTP_SSL(self.__host) as server:
                server.login(self.__user, self.__passwd)
                server.sendmail(self.__user, addressee, message.as_string())
        except smtplib.SMTPConnectError as e:
            logs.error(f'Server connection failed: {e}')
        except smtplib.SMTPAuthenticationError as e:
            logs.error(f'Authentication failed, check account or app password: {e}')
        except smtplib.SMTPSenderRefused as e:
            logs.error(f'Sender refused: {e}')
        except smtplib.SMTPDataError as e:
            logs.error(f'Message rejected or marked as spam: {e}')
        except Exception as e:
            logs.error(f'Email sending error: {e}')
        else:
            logs.info('Email sent successfully!')


class BuildEmail(SendEmail):
    """Send test report email"""

    def main(self, success, failed, error, not_running, atta_file=None):
        """
        Build test report content and send email
        :param success: list of passed cases
        :param failed: list of failed cases
        :param error: list of error cases
        :param not_running: list of not executed cases
        :param atta_file: attachment path
        """
        total = len(success) + len(failed) + len(error) + len(not_running)
        execute_case = len(success) + len(failed)
        pass_rate = f"{len(success) / execute_case * 100:.2f}%" if execute_case else "0.00%"
        fail_rate = f"{len(failed) / execute_case * 100:.2f}%" if execute_case else "0.00%"
        error_rate = f"{len(error) / execute_case * 100:.2f}%" if execute_case else "0.00%"

        subject = conf.get_section_for_data('EMAIL', 'subject')
        addressee = conf.get_section_for_data('EMAIL', 'addressee')

        content = (
            f"***API Test Report: Total {total} cases, "
            f"Passed {len(success)}, Failed {len(failed)}, Error {len(error)}, "
            f"Not run {len(not_running)}, Pass rate {pass_rate}, Fail rate {fail_rate}, Error rate {error_rate}.\n"
            f"See attachment for details."
        )

        self.build_content(subject, content, addressee, atta_file)
