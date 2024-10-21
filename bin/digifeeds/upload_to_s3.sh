#! /bin/bash

# For push gateway
START_TIME=$(date '+%s')

###########
# Directory this script lives in
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

source $SCRIPT_DIR/upload_to_s3_functions.sh


if [[ $APP_ENV != "test" ]]; then
  # CONFIG
  # Variables contained in the config file:
  #
  # input_directory: path to the input directory
  # processed_directory: path to the directory  of processed files+%
  # digifeeds_bucket: rclone remote for the digifeeds bucket
  #
  # timestamp: used for testing timestamps; should be ommited in production
  CONFIG_FILE=${1:-$SCRIPT_DIR/upload_to_s3.config}
  source $CONFIG_FILE

  main
fi