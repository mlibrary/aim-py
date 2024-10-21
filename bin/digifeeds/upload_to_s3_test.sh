#!/usr/bin/bats
export BATS_LIB_PATH=${BATS_LIB_PATH:-"/usr/lib/bats"}
bats_load_library bats-support
bats_load_library bats-assert
bats_load_library bats-file


setup() {
  load $SHELLMOCK_PATH
  SCRATCH_PATH="/tmp/upload_to_s3"
  CONFIG_PATH=$SCRATCH_PATH/upload_to_s3.config
  #SUBJECT="$BATS_TEST_DIRNAME/upload_to_s3.sh $CONFIG_PATH"
  SUBJECT=main


  mkdir $SCRATCH_PATH

  INPUT_DIR=$SCRATCH_PATH/input
  PROCESSED_DIR=$SCRATCH_PATH/processed

  BARCODE_1="30123456789012"
  BARCODE_2="40123456789012"
  TIMESTAMP="YYYY-MM-DD_hh-mm-ss"

  mkdir $INPUT_DIR
  mkdir $PROCESSED_DIR

  mkdir $INPUT_DIR/$BARCODE_1
  touch $INPUT_DIR/$BARCODE_1/01234567.tif
  touch $INPUT_DIR/$BARCODE_1/01234567.jp2
  touch $INPUT_DIR/$BARCODE_1/checksum.md5
  touch $INPUT_DIR/$BARCODE_1/Thumbs.db
  touch $INPUT_DIR/$BARCODE_1/some_other_file.tif

  mkdir $INPUT_DIR/$BARCODE_2
  touch $INPUT_DIR/$BARCODE_2/01234567.tif

  ## Config that's in main.
  input_directory="$INPUT_DIR"
  processed_directory="$PROCESSED_DIR"
  digifeeds_bucket="digifeeds_bucket"
  timestamp=$TIMESTAMP
  send_metrics="false"
  APP_ENV="test"

  load "$BATS_TEST_DIRNAME/upload_to_s3.sh"
}

teardown() {
  rm -r $SCRATCH_PATH
}

@test "It Works" {
  shellmock new rclone 
  shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
  shellmock config rclone 0 1:check regex-2:$INPUT_DIR regex-3:^digifeeds_bucket:
  run $SUBJECT
  
  assert_success

  assert_file_exists $PROCESSED_DIR/${TIMESTAMP}_${BARCODE_1}.zip
  assert_file_exists $PROCESSED_DIR/${TIMESTAMP}_${BARCODE_2}.zip

  assert_dir_exists $PROCESSED_DIR/${TIMESTAMP}_${BARCODE_1}
  assert_dir_exists $PROCESSED_DIR/${TIMESTAMP}_${BARCODE_2}
  shellmock assert expectations rclone
}

@test "It filters the appropriate files" {
  shellmock new rclone 
  shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
  shellmock config rclone 0 1:check regex-2:$INPUT_DIR regex-3:^digifeeds_bucket:

  run $SUBJECT
  cd $BATS_TEST_TMPDIR
  mv $PROCESSED_DIR/${TIMESTAMP}_${BARCODE_1}.zip ./
  unzip -q  ${TIMESTAMP}_${BARCODE_1}.zip 
  assert_file_exists '01234567.jp2'
  assert_file_exists '01234567.tif'
  assert_file_exists 'checksum.md5'
  assert_file_not_exists 'Thumbs.db'
  assert_file_not_exists 'some_other_file.tif'

  shellmock assert expectations rclone
}

# This test shows that `shopt -s  nullglob` in necessary`
@test "Emtpy input directory works" {
  rm -r $INPUT_DIR/$BARCODE_1
  rm -r $INPUT_DIR/$BARCODE_2

  run $SUBJECT
  assert_success
}

@test "Failed zip" {
  shellmock new zip 
  shellmock config zip 1 
  run $SUBJECT
  assert_output --partial "ERROR: Failed to zip $BARCODE_1"
  assert_output --partial "ERROR: Failed to zip $BARCODE_2"
  assert_output --partial "INFO: Total files processed:\t0"
  assert_output --partial "INFO: Total errors:\t2"
  assert_output --partial "INFO: Total errors uploading to S3:\t0"
  shellmock assert expectations zip
}

@test "Failed copy records error and moves on" {
  shellmock new rclone 
  shellmock config rclone 1 1:copy regex-3:^digifeeds_bucket: <<< "Rclone error mock: Failed to copy"
  run $SUBJECT
  assert_output --partial "ERROR: Failed to copy $BARCODE_1"
  assert_output --partial "ERROR: Failed to copy $BARCODE_2"
  assert_output --partial "INFO: Total files processed:\t0"
  assert_output --partial "INFO: Total errors:\t2"
  assert_output --partial "INFO: Total errors uploading to S3:\t2"
  shellmock assert expectations rclone
}

@test "Failed on S3 verification and moves on" {
  shellmock new rclone 
  shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
  shellmock config rclone 1 1:check regex-2:$INPUT_DIR regex-3:^digifeeds_bucket:
  run $SUBJECT
  assert_output --partial "ERROR: $BARCODE_1 not found in S3"
  assert_output --partial "ERROR: $BARCODE_2 not found in S3"
  assert_output --partial "INFO: Total files processed:\t0"
  assert_output --partial "INFO: Total errors:\t2"
  assert_output --partial "INFO: Total errors uploading to S3:\t2"
  shellmock assert expectations rclone
}
@test "print_metrics" {
  shellmock new pushgateway_advanced
  shellmock config pushgateway_advanced 0 <<< 5
  run print_metrics 1 2 3
  assert_output --partial "aim_digifeeds_upload_to_s3_files_processed_total 6"
  assert_output --partial "aim_digifeeds_upload_to_s3_upload_errors_total 7"
  assert_output --partial "aim_digifeeds_upload_to_s3_errors_total 8"
  shellmock assert expectations pushgateway_advanced
  
}

@test "verify_zip success" {
   zip_it $INPUT_DIR/$BARCODE_1
   run verify_zip $INPUT_DIR/$BARCODE_1
   assert_success
}

@test "verify_zip fail" {
   zip_it $INPUT_DIR/$BARCODE_2
   mv $INPUT_DIR/$BARCODE_2.zip $INPUT_DIR/$BARCODE_1.zip
   run verify_zip $INPUT_DIR/$BARCODE_1
   assert_failure
}