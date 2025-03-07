#!/usr/bin/bats
export BATS_LIB_PATH=${BATS_LIB_PATH:-"/usr/lib/bats"}
bats_load_library bats-support
bats_load_library bats-assert
bats_load_library bats-file

setup() {
    load "$SHELLMOCK_PATH"
    SCRATCH_PATH="/tmp/upload_to_s3"
    SUBJECT=main

    mkdir $SCRATCH_PATH

    INPUT_DIR=$SCRATCH_PATH/input
    WORKING_DIR=$SCRATCH_PATH/working
    PROCESSED_DIR=$SCRATCH_PATH/processed

    BARCODE_1="30000000189012"
    BARCODE_2="40000000189012"
    TIMESTAMP="YYYY-MM-DD_hh-mm-ss"

    mkdir $INPUT_DIR
    mkdir $PROCESSED_DIR
    mkdir $WORKING_DIR

    mkdir $INPUT_DIR/$BARCODE_1
    touch $INPUT_DIR/$BARCODE_1/00000001.tif
    touch $INPUT_DIR/$BARCODE_1/00000002.jp2
    touch $INPUT_DIR/$BARCODE_1/checksum.md5
    touch $INPUT_DIR/$BARCODE_1/Thumbs.db
    touch $INPUT_DIR/$BARCODE_1/some_other_file.tif

    mkdir $INPUT_DIR/$BARCODE_2
    touch $INPUT_DIR/$BARCODE_2/00000001.tif

    ## Config that's in main.
    export input_directory="$INPUT_DIR"
    export processed_directory="$PROCESSED_DIR"
    export working_directory="$WORKING_DIR"
    export digifeeds_bucket="digifeeds_bucket"
    export timestamp=$TIMESTAMP
    export send_metrics="false"
    export APP_ENV="test"

    load "$BATS_TEST_DIRNAME/upload_to_s3.sh"
}

teardown() {
    rm -r "$SCRATCH_PATH"
}

@test "exits without input_directory" {
    unset input_directory
    run "${BATS_TEST_DIRNAME}/upload_to_s3.sh"
    assert_failure
}
@test "exits without processed_directory" {
    unset processed_directory
    run "${BATS_TEST_DIRNAME}/upload_to_s3.sh"
    assert_failure
}
@test "exits without digifeeds_bucket" {
    unset digifeeds_bucket
    run "${BATS_TEST_DIRNAME}/upload_to_s3.sh"
    assert_failure
}

@test "It Works" {
    shellmock new rclone
    shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
    shellmock config rclone 0 1:check regex-2:"$WORKING_DIR" regex-3:^digifeeds_bucket:
    run $SUBJECT

    assert_success

    assert_file_exists "$PROCESSED_DIR"/"${TIMESTAMP}"_"${BARCODE_1}".zip
    assert_file_exists "$PROCESSED_DIR"/"${TIMESTAMP}"_"${BARCODE_2}".zip

    assert_dir_exists "$PROCESSED_DIR"/"${TIMESTAMP}"_"${BARCODE_1}"
    assert_dir_exists "$PROCESSED_DIR"/"${TIMESTAMP}"_"${BARCODE_2}"
    shellmock assert expectations rclone
}

@test "It filters the appropriate files" {
    shellmock new rclone
    shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
    shellmock config rclone 0 1:check regex-2:"$WORKING_DIR" regex-3:^digifeeds_bucket:

    run $SUBJECT
    cd "$BATS_TEST_TMPDIR"
    mv "$PROCESSED_DIR/${TIMESTAMP}_${BARCODE_1}.zip" ./
    unzip -q "${TIMESTAMP}_${BARCODE_1}.zip"
    assert_file_exists '00000001.tif'
    assert_file_exists '00000002.jp2'
    assert_file_exists 'checksum.md5'
    assert_file_not_exists 'Thumbs.db'
    assert_file_not_exists 'some_other_file.tif'

    shellmock assert expectations rclone
}

# This test shows that `shopt -s  nullglob` in necessary`
@test "Emtpy input directory works" {
    rm -r "${INPUT_DIR:?}/${BARCODE_1:?}"
    rm -r "${INPUT_DIR:?}/${BARCODE_2:?}"

    run $SUBJECT
    assert_success
}

@test "verify_image_order sucess" {
    run verify_image_order 00000001.tif 00000003.jp2 00000002.tif
    assert_success
}

@test "verify_image_order failure" {
    run verify_image_order 00000001.tif 00000003.tif 00000004.jp2
    assert_failure
}

@test "Failed image order" {
    shellmock new rclone
    shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
    shellmock config rclone 0 1:check regex-2:"$WORKING_DIR" regex-3:^digifeeds_bucket:
    touch "$INPUT_DIR"/"$BARCODE_1"/00000004.jp2
    run $SUBJECT
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_1"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_1.zip"
    assert_output --partial "ERROR: Image order incorrect for $BARCODE_1"
    assert_output --partial "INFO: Total files processed: 1"
    assert_output --partial "INFO: Total errors: 1"
    assert_output --partial "INFO: Total errors image order: 1"
    assert_output --partial "INFO: Total errors uploading to S3: 0"
    shellmock assert expectations rclone
}

@test "Failed zip" {
    shellmock new zip
    shellmock config zip 1
    run $SUBJECT
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_1"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_1.zip"
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_2"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_2.zip"
    assert_output --partial "ERROR: Failed to zip $BARCODE_1"
    assert_output --partial "ERROR: Failed to zip $BARCODE_2"
    assert_output --partial "INFO: Total files processed: 0"
    assert_output --partial "INFO: Total errors image order: 0"
    assert_output --partial "INFO: Total errors: 2"
    assert_output --partial "INFO: Total errors uploading to S3: 0"
    shellmock assert expectations zip
}

@test "Failed copy records error and moves on" {
    shellmock new rclone
    shellmock config rclone 1 1:copy regex-3:^digifeeds_bucket: <<<"Rclone error mock: Failed to copy"
    run $SUBJECT
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_1"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_1.zip"
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_2"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_2.zip"
    assert_output --partial "ERROR: Failed to copy $BARCODE_1"
    assert_output --partial "ERROR: Failed to copy $BARCODE_2"
    assert_output --partial "INFO: Total files processed: 0"
    assert_output --partial "INFO: Total errors image order: 0"
    assert_output --partial "INFO: Total errors: 2"
    assert_output --partial "INFO: Total errors uploading to S3: 2"
    shellmock assert expectations rclone
}

@test "Failed on S3 verification and moves on" {
    shellmock new rclone
    shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
    shellmock config rclone 1 1:check regex-2:"$WORKING_DIR" regex-3:^digifeeds_bucket:
    run $SUBJECT
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_1"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_1.zip"
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_2"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_2.zip"
    assert_output --partial "ERROR: $BARCODE_1 not found in S3"
    assert_output --partial "ERROR: $BARCODE_2 not found in S3"
    assert_output --partial "INFO: Total files processed: 0"
    assert_output --partial "INFO: Total errors image order: 0"
    assert_output --partial "INFO: Total errors: 2"
    assert_output --partial "INFO: Total errors uploading to S3: 2"
    shellmock assert expectations rclone
}
@test "Fails on copying barcode folder to working directory and moves on" {
    shellmock new cp
    shellmock config cp 1 regex-2:"$INPUT_DIR" <<<"Error"
    run $SUBJECT
    assert_output --partial "ERROR: Copying $BARCODE_1 to working directory failed"
    assert_output --partial "ERROR: Copying $BARCODE_2 to working directory failed"
    assert_output --partial "INFO: Total files processed: 0"
    assert_output --partial "INFO: Total errors image order: 0"
    assert_output --partial "INFO: Total errors: 2"
    assert_output --partial "INFO: Total errors uploading to S3: 0"
    shellmock assert expectations cp
}

@test "Fails on copying zip to processed directory and moves on" {
    shellmock new rclone
    shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
    shellmock config rclone 0 1:check regex-2:"$WORKING_DIR" regex-3:^digifeeds_bucket:
    cp -r "$INPUT_DIR"/* "$WORKING_DIR"
    shellmock new cp
    shellmock config cp 0 regex-2:"$INPUT_DIR"
    shellmock config cp 1 regex-2:.zip <<<"Error"
    run $SUBJECT
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_1"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_1.zip"
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_2"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_2.zip"
    assert_output --partial "ERROR: Failed to copy ${BARCODE_1}.zip to processed"
    assert_output --partial "ERROR: Failed to copy ${BARCODE_2}.zip to processed"
    assert_output --partial "INFO: Total files processed: 0"
    assert_output --partial "INFO: Total errors image order: 0"
    assert_output --partial "INFO: Total errors: 2"
    assert_output --partial "INFO: Total errors uploading to S3: 0"
    shellmock assert expectations cp
    shellmock assert expectations rclone
}
@test "Fails on copying working folder to processed directory and moves on" {
    shellmock new rclone
    shellmock config rclone 0 1:copy regex-3:^digifeeds_bucket:
    shellmock config rclone 0 1:check regex-2:"$WORKING_DIR" regex-3:^digifeeds_bucket:
    cp -r "$INPUT_DIR"/* "$WORKING_DIR"
    shellmock new cp
    shellmock config cp 0 regex-2:"$INPUT_DIR"
    shellmock config cp 0 regex-2:.zip
    shellmock config cp 1 <<<"Error"
    run $SUBJECT
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_1"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_1.zip"
    assert_dir_not_exists "$WORKING_DIR/$BARCODE_2"
    assert_file_not_exists "$WORKING_DIR/$BARCODE_2.zip"
    assert_output --partial "ERROR: Failed to copy ${BARCODE_1} to processed"
    assert_output --partial "ERROR: Failed to copy ${BARCODE_2} to processed"
    assert_output --partial "INFO: Total files processed: 0"
    assert_output --partial "INFO: Total errors image order: 0"
    assert_output --partial "INFO: Total errors: 2"
    assert_output --partial "INFO: Total errors uploading to S3: 0"
    shellmock assert expectations cp
    shellmock assert expectations rclone
}

@test "print_metrics" {
    shellmock new pushgateway_advanced
    shellmock config pushgateway_advanced 0 <<<5
    run print_metrics 1 2 3 4
    assert_output --partial "aim_digifeeds_upload_to_aws_files_processed_total 6"
    assert_output --partial "aim_digifeeds_upload_to_aws_image_order_errors 2"
    assert_output --partial "aim_digifeeds_upload_to_aws_upload_errors 3"
    assert_output --partial "aim_digifeeds_upload_to_aws_errors 4"
    shellmock assert expectations pushgateway_advanced

}

@test "verify_zip success" {
    zip_it "$INPUT_DIR"/"$BARCODE_1"
    run verify_zip "$INPUT_DIR"/"$BARCODE_1"
    assert_success
}

@test "verify_zip fail" {
    zip_it "$INPUT_DIR"/"$BARCODE_2"
    mv "$INPUT_DIR"/"$BARCODE_2".zip "$INPUT_DIR"/"$BARCODE_1".zip
    run verify_zip "$INPUT_DIR"/"$BARCODE_1"
    assert_failure
}
