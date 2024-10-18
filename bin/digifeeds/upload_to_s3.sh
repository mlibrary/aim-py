#! /bin/bash 
set -e #exit on error

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

###########
# CONFIG
# Variables contained in the config file:
#
# input_directory: path to the input directory
# processed_directory: path to the directory  of processed files
# work_directory: path to the directory to do the processing of files
# log_directory: path to store log and metrics files
# digifeeds_bucket: rclone remote for the digifeeds bucket
#
# timestamp: used for testing timestamps; should be ommited in production
CONFIG_FILE=${1:-$SCRIPT_DIR/upload_to_s3.config}
source $CONFIG_FILE

TIMESTAMP=${timestamp:-$(date +%F_%H-%M-%S)} #YYY-MM-DD_hh-mm-ss

# matches .tif and .jp2 files with 8 digit file names that start with 0 OR
# checksum.md5 files
# examples that match: 
#   01234567.tif
#   01234567.jp2
#   checksum.md5 
IMGAWK='/^(0[0-9][0-9][0-9][0-9][0-9][0-9][0-9]\.(tif|jp2)|checksum\.md5)$/'

#This is so that the script works on empty directories. 
shopt -s nullglob

barcode_directories=($input_directory/*/)

# move directories; Limit chance of users interacting with files to be moved.
for barcode_path in "${barcode_directories[@]}"; do
    # turns "/some/path/to/some_barcode/" into "some_barcode"
     barcode=$(basename ${barcode_path%%/})

     mv $input_directory/$barcode $work_directory/$barcode
done

# works on barcodes
for barcode_path in "${barcode_directories[@]}"; do
     barcode=$(basename ${barcode_path%%/})

    echo "hello"
     cd $work_directory/$barcode 
     ls | awk "$IMGAWK" | xargs zip -rq $work_directory/$barcode.zip
     cd -

     rclone copy $workdirectory/$barcode.zip $digifeeds_bucket:$barcode.zip

     mv $work_directory/$barcode.zip $processed_directory/${TIMESTAMP}_${barcode}.zip
     mv $work_directory/$barcode $processed_directory/${TIMESTAMP}_${barcode}
done
