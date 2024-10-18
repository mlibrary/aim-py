#!/usr/bin/bats
export BATS_LIB_PATH=${BATS_LIB_PATH:-"/usr/lib/bats"}
bats_load_library bats-support
bats_load_library bats-assert
bats_load_library bats-file


setup() {
  load $SHELLMOCK_PATH
  SCRATCH_PATH="/tmp/upload_to_s3"
  CONFIG_PATH=$SCRATCH_PATH/upload_to_s3.config
  SUBJECT="$BATS_TEST_DIRNAME/upload_to_s3.sh $CONFIG_PATH"

  mkdir $SCRATCH_PATH

  INPUT_DIR=$SCRATCH_PATH/input
  PROCESSED_DIR=$SCRATCH_PATH/processed
  LOG_DIR=$SCRATCH_PATH/log
  WORK_DIR=$SCRATCH_PATH/work

  BARCODE_1="30123456789012"
  BARCODE_2="40123456789012"
  TIMESTAMP="YYYY-MM-DD_hh-mm-ss"

  mkdir $INPUT_DIR
  mkdir $PROCESSED_DIR
  mkdir $LOG_DIR
  mkdir $WORK_DIR

  mkdir $INPUT_DIR/$BARCODE_1
  touch $INPUT_DIR/$BARCODE_1/01234567.tif
  touch $INPUT_DIR/$BARCODE_1/01234567.jp2
  touch $INPUT_DIR/$BARCODE_1/checksum.md5
  touch $INPUT_DIR/$BARCODE_1/Thumbs.db
  touch $INPUT_DIR/$BARCODE_1/some_other_file.tif

  mkdir $INPUT_DIR/$BARCODE_2
  touch $INPUT_DIR/$BARCODE_2/01234567.tif

  cat <<EOF >$CONFIG_PATH
input_directory="$INPUT_DIR"
processed_directory="$PROCESSED_DIR"
work_directory="$WORK_DIR"
log_directory="$LOG_DIR"
digifeeds_bucket="digifeeds_bucket"
timestamp=$TIMESTAMP
EOF

}

teardown() {
  rm -r $SCRATCH_PATH

}


@test "It Works" {
  shellmock new rclone 
  shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
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

