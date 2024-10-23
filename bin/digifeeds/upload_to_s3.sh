#! /bin/bash

###########
# CONSTANTS
###########

# For push gateway
START_TIME=$(date '+%s')

# Directory this script lives in
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

APP_ENV=${APP_ENV:-"production"}

if [[ $APP_ENV != "test" ]]; then
  # CONFIG
  # Variables contained in the config file:
  #
  # input_directory: path to the input directory
  # processed_directory: path to the directory  of processed files+%
  # digifeeds_bucket: rclone remote for the digifeeds bucket
  #
  # timestamp: used for testing timestamps; should be ommited in production
  # send_metrics: when "false" metrics don't get sent;
  # APP_ENV: when "test" the main script is not executed
  CONFIG_FILE=${1:-$SCRIPT_DIR/upload_to_s3.config}
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi
if ! input_directory=${input_directory:?}; then exit 1; fi
if ! processed_directory=${processed_directory:?}; then exit 1; fi
if ! digifeeds_bucket=${digifeeds_bucket:?}; then exit 1; fi
send_metrics=${send_metrics:-"true"}

# matches .tif and .jp2 files with 8 digit file names that start with 0 OR
# checksum.md5 files
# examples that match:
#   01234567.tif
#   01234567.jp2
#   checksum.md5
IMGAWK='/^(0[0-9][0-9][0-9][0-9][0-9][0-9][0-9]\.(tif|jp2)|checksum\.md5)$/'

# For push gateway
JOB_NAME="aim_digifeeds_upload_to_aws"

###########
# COUNTERS
###########
files_processed_total=0
image_order_errors_total=0
upload_errors_total=0
errors_total=0

###########
# FUNCTIONS
###########

log_info() {
  echo "$(date --rfc-3339=seconds) - INFO: $*"
}

log_error() {
  echo "$(date --rfc-3339=seconds) - ERROR: $*"
}
log_debug() {
  [[ ${DEBUG:-false} == "true" ]] && echo "$(date --rfc-3339=seconds) - DEBUG: $*"
}

#equivalent to ls
list_files() {
  local path=$1
  find "$path" -maxdepth 1 ! -printf '%P\n'
}

# Gets the last count from a job in the push gateway push gateway
last_count() {
  local metric=$1
  pushgateway_advanced -j $JOB_NAME -q "${metric}"
}

verify_image_order() {
  #Sort the array
  mapfile -t sorted < <(printf '%s\n' "$@" | sort)

  local cnt=0
  for arg in "${sorted[@]}"; do
    cnt=$((cnt + 1))
    int=${arg:0:8}
    [ $((10#$int)) != $cnt ] && return 1
  done
  return 0
}

zip_it() {
  local barcode_path=$1
  cd "$barcode_path" || return 1
  list_files . | awk "$IMGAWK" | xargs zip -rq "$barcode_path".zip
  local zip_return=$?
  #Go back to  previous directory; Don't print the output.
  cd - >/dev/null || return 1
  return $zip_return
}

verify_zip() {
  local barcode_path=$1

  local files_in_dir
  if ! files_in_dir=$(list_files "$barcode_path" | awk "$IMGAWK" | sort); then
    return 1
  fi
  local files_in_zip
  if ! files_in_zip=$(zipinfo -1 "$barcode_path".zip | sort); then
    return 1
  fi

  if [ "$files_in_dir" == "$files_in_zip" ]; then
    return 0
  else
    return 1
  fi
}

print_metrics() {
  local fp_current_total=$1
  local image_order_errors_current_total=$2
  local upload_errors_current_total=$3
  local errors_current_total=$4

  local fp_metric="${JOB_NAME}_files_processed_total"
  local fp_last
  fp_last=$(last_count $fp_metric)
  local fp_total=$((fp_last + fp_current_total))

  local image_order_errors_metric="${JOB_NAME}_image_order_errors_total"
  local image_order_errors_last
  image_order_errors_last=$(last_count $image_order_errors_metric)
  local image_order_errors_total=$((image_order_errors_last + image_order_errors_current_total))

  local upload_errors_metric="${JOB_NAME}_upload_errors_total"
  local upload_errors_last
  upload_errors_last=$(last_count $upload_errors_metric)
  local upload_errors_total=$((upload_errors_last + upload_errors_current_total))

  local errors_metric="${JOB_NAME}_errors_total"
  local errors_last
  errors_last=$(last_count $errors_metric)
  local errors_total=$((errors_last + errors_current_total))

  cat <<EOMETRICS
# HELP ${fp_metric} Count of digifeeds zip files sent to S3
# TYPE ${fp_metric} counter
$fp_metric $fp_total
# HELP ${image_order_errors_metric} Count of folders where there are missing pages of images 
# TYPE ${image_order_errors_metric} counter
${image_order_errors_metric} $image_order_errors_total
# HELP ${upload_errors_metric} Count of errors when uploading digifeeds zip files to S3
# TYPE ${upload_errors_metric} counter
${upload_errors_metric} $upload_errors_total
# HELP ${errors_metric} Count of all errors relating ot uploading digifeeds files sent to S3
# TYPE ${errors_metric} counter
${errors_metric} $errors_total
EOMETRICS
}

main() {
  TIMESTAMP=${timestamp:-$(date +%F_%H-%M-%S)} #YYY-MM-DD_hh-mm-ss

  #This is so that the script works on empty directories.
  shopt -s nullglob

  for barcode_path in "${input_directory}"/*/; do
    local barcode
    barcode=$(basename "${barcode_path%%/}")

    log_info "Copying $barcode"

    log_debug "Verifying image order $barcode"
    #8 digits, ends in .tif or .jp2
    filter_regex='[[:digit:]]{8}\.tif$|[[:digit:]]{8}\.jp2$'
    local image_list
    image_list=$(list_files "$barcode_path" | grep -E "$filter_regex")
    if ! verify_image_order "$image_list"; then
      log_error "Image order incorrect for $barcode"
      image_order_errors_total=$((image_order_errors_total + 1))
      errors_total=$((errors_total + 1))
      continue
    fi

    log_debug "Zipping $barcode"
    if ! zip_it "$input_directory"/"$barcode"; then
      log_error "Failed to zip $barcode"
      errors_total=$((errors_total + 1))
      continue
    fi

    log_debug "Verifying zip of $barcode"
    if ! verify_zip "$input_directory"/"$barcode"; then
      log_error "$barcode.zip does not contain the correct files"
      errors_total=$((errors_total + 1))
      continue
    fi

    log_debug "Sending $barcode to S3"
    if ! rclone copy "$input_directory"/"$barcode".zip "$digifeeds_bucket":; then
      log_error "Failed to copy $barcode"
      upload_errors_total=$((upload_errors_total + 1))
      errors_total=$((errors_total + 1))
      continue
    fi

    log_debug "Verifying barcode in S3"
    if ! rclone check "$input_directory"/"$barcode".zip "$digifeeds_bucket":; then
      log_error "$barcode not found in S3"
      upload_errors_total=$((upload_errors_total + 1))
      errors_total=$((errors_total + 1))
      continue
    fi

    log_info "Moving $barcode to processed"
    mv "$input_directory"/"$barcode".zip "$processed_directory"/"${TIMESTAMP}"_"${barcode}".zip
    mv "$input_directory"/"$barcode" "$processed_directory"/"${TIMESTAMP}"_"${barcode}"
    files_processed_total=$((files_processed_total + 1))
  done

  log_info "Total files processed: $files_processed_total"
  log_info "Total errors image order: $image_order_errors_total "
  log_info "Total errors uploading to S3: $upload_errors_total"
  log_info "Total errors: $errors_total"
}

if [[ $APP_ENV != "test" ]]; then

  log_info "=====Start $(date)====="

  main

  if [ "$send_metrics" != "false" ]; then
    print_metrics $files_processed_total $image_order_errors_total $upload_errors_total $errors_total | /usr/local/bin/pushgateway_advanced -j $JOB_NAME
    /usr/local/bin/pushgateway -j $JOB_NAME -b "$START_TIME"
  fi
  log_info "=====End $(date)====="
fi
