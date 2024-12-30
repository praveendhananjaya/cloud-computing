from pymongo import MongoClient
import pandas as pd
import boto3
import psycopg2
from io import StringIO
import os
# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI",
                      "mongodb+srv://healthsync.qntlu.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=HealthSync")
MONGO_CERT_PATH = os.getenv("MONGO_CERT_PATH", "X509-cert-8433791428290760769.pem")

DB_NAME = os.getenv("DB_NAME", "MediTrack")
MONGO_COLLECTION = "appointments"

# AWS S3 and Redshift Config
AWS_ACCESS_KEY = "AKIAT7H2GGFCFLWKSJN6"
AWS_SECRET_KEY = "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"
S3_BUCKET_NAME = "migration-mongodb"
S3_FILE_NAME = "mongo_to_redshift.csv"
REDSHIFT_HOST = "default-workgroup.273255117124.us-east-1.redshift-serverless.amazonaws.com"
REDSHIFT_PORT = 5439
REDSHIFT_DB = "dev"
REDSHIFT_USER = "service_role"
REDSHIFT_PASSWORD = 'Y8/dUp7VrF$"R9f.<`mS+!'


def fetch_mongo_data():
    # Connect to MongoDB and fetch data
    client = MongoClient(MONGO_URI , tls=True, tlsCertificateKeyFile=MONGO_CERT_PATH)
    db = client[DB_NAME]
    collection = db[MONGO_COLLECTION]
    data = list(collection.find())
    client.close()
    return data

def transform_data(data):
    # Transform MongoDB data into a Pandas DataFrame
    df = pd.DataFrame(data)
    if "_id" in df.columns:
        df.drop(columns=["_id"], inplace=True)  # Remove MongoDB's ObjectId
    return df

def upload_to_s3(df):
    # Save DataFrame to CSV and upload to S3
    s3_client = boto3.client(
        "s3", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY
    )
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_NAME, Body=csv_buffer.getvalue())

def load_to_redshift():
    copy_command = f"""
            COPY {MONGO_COLLECTION}
            FROM 's3://{S3_BUCKET_NAME}/{S3_FILE_NAME}'
            IAM_ROLE 'arn:aws:iam::273255117124:user/AWS_ser/service_role'
            CSV IGNOREHEADER 1;
        """
    print(copy_command)
    # Connect to Redshift and execute COPY command
    conn = psycopg2.connect(
        host=REDSHIFT_HOST,
        port=REDSHIFT_PORT,
        dbname=REDSHIFT_DB,
        user=REDSHIFT_USER,
        password=REDSHIFT_PASSWORD
    )
    cursor = conn.cursor()

    cursor.execute(copy_command)
    conn.commit()
    cursor.close()
    conn.close()

def main():
    # Main workflow
    print("Fetching data from MongoDB...")
    mongo_data = fetch_mongo_data()

    print("Transforming data...")
    transformed_data = transform_data(mongo_data)

    print("Uploading data to S3...")
    upload_to_s3(transformed_data)

    print("Loading data into Redshift...")
    load_to_redshift()

    print("ETL Process Completed!")

if __name__ == "__main__":
    main()
