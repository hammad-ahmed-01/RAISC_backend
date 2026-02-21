import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
load_dotenv()
def send_test_email():
    # Specify your AWS Region (e.g., "us-east-1", "eu-central-1")
    aws_region = "ap-southeast-2" 
    
    # The sender address can be any email on your verified domain
    sender = os.getenv("SENDER_EMAIL")
    
    # The recipient must be a verified identity while in the sandbox
    recipient = "usman.javaid2209@gmail.com"
    
    subject = "Amazon SES Test Email "
    
    # The email body for recipients with non-HTML email clients
    body_text = ("Amazon SES Test\r\n"
                 "This email was sent with Amazon SES using the AWS SDK for Python (Boto3)."
                )
                
    # The HTML body of the email
    body_html = """<html>
    <head></head>
    <body>
      <h1>Welcome to MediPro</h1>
      <p>This email was sent with Amazon SES using the 
        <a href='https://aws.amazon.com/sdk-for-python/'>AWS SDK for Python (Boto3)</a>.</p>
    </body>
    </html>
    """
    
    # The character encoding for the email
    charset = "UTF-8"
    
    # Create a new SES client
    client = boto3.client('ses', region_name=aws_region)
    
    try:
        # Provide the contents of the email
        response = client.send_email(
            Destination={
                'ToAddresses': [recipient],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': charset,
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': charset,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=sender,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print(f"Email sent! Message ID: {response['MessageId']}")

if __name__ == '__main__':
    send_test_email()