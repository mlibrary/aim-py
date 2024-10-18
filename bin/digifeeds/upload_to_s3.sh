#! /bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

###########
# CONFIG
# Variables contained in the config file:
#
# input_directory: path to the input directory
# processed_directory: path to the directory  of processed files
# work_directory: path to the directory to do the processing of files
# log_directory: path to store log and metrics files
CONFIG_FILE=${1:-$SCRIPT_DIR/upload_to_s3.config}

source $CONFIG_FILE
TIMESTAMP=${timestamp:-$(date +%F_%H-%M-%S)} #YYY-MM-DD_hh-mm-ss

#This is so that the script works on empty directories. 
# shopt -s nullglob

barcode_directories=($input_directory/*/)
for barcode_path in "${barcode_directories[@]}"; do
    # turns "/some/path/to/some_barcode/" into "some_barcode"
     barcode=$(basename ${barcode_path%%/})
     mv $input_directory/$barcode $work_directory/$barcode

     zip -rq $work_directory/$barcode $work_directory/$barcode

     mv $work_directory/$barcode.zip $processed_directory
     mv $work_directory/$barcode $processed_directory/
done

echo $TIMESTAMP
