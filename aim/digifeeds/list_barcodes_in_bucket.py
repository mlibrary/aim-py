import boto3
from aim.services import S


def list_barcodes_in_bucket():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=S.digifeeds_s3_access_key,
        aws_secret_access_key=S.digifeeds_s3_secret_access_key,
    )
    prefix = S.digifeeds_s3_input_path + "/"
    response = s3.list_objects_v2(
        Bucket=S.digifeeds_s3_bucket,
        Prefix=prefix,
        Delimiter="/",
    )
    paths = [object["Prefix"] for object in response["CommonPrefixes"]]
    barcodes = [path.split("/")[1] for path in paths]
    return barcodes
