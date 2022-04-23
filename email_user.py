import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import os

# create message object instance
# setup the parameters of the message

def email_the_user(msg_to, file):
    msg = MIMEMultipart()

    # setup the parameters of the message
    password = "gagan2002"
    msg['From'] = "kummurgagan@gmail.com"
    msg['Subject'] = "Your QR Code"
    # attach image to message body
    with open(file, 'rb') as f:
        img_data = f.read()
    text = MIMEText("please save this image for later uses")
    msg.attach(text)
    image = MIMEImage(img_data, name=os.path.basename(file))
    msg.attach(image)

    # create server
    server = smtplib.SMTP('smtp.gmail.com: 587')

    server.starttls()

    # Login Credentials for sending the mail
    server.login(msg['From'], password)

    # send the message via the server.
    server.sendmail(msg['From'], msg_to, msg.as_string())

    server.quit()
    return "emailed"
if __name__ == '__main__':
    msg_to = "gckummur@gmail.com"
    file = "31993a36500e66d26209597003729a6c23294bf7c0e8744c9b3404d635d275b5.png"
    email_the_user(msg_to,file)
