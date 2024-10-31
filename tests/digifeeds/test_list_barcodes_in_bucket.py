import boto3
from moto import mock_aws
from aim.services import S
from aim.digifeeds.list_barcodes_in_bucket import list_barcodes_in_bucket


@mock_aws
def test_list_barcodes_in_bucket():
    conn = boto3.resource(
        "s3",
        aws_access_key_id=S.digifeeds_s3_access_key,
        aws_secret_access_key=S.digifeeds_s3_secret_access_key,
    )
    conn.create_bucket(Bucket=S.digifeeds_s3_bucket)

    barcode1 = conn.Object(
        S.digifeeds_s3_bucket, f"{S.digifeeds_s3_input_path}/barcode1.zip"
    )
    barcode1.put(Body="some text")
    barcode2 = conn.Object(
        S.digifeeds_s3_bucket, f"{S.digifeeds_s3_input_path}/barcode2.zip"
    )
    barcode2.put(Body="some text")

    result = list_barcodes_in_bucket()
    assert result == ["barcode1", "barcode2"]
