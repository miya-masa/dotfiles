#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'

INFLUX_CLI_VERSION=2.2.0

if [[ ! -e /usr/local/bin/influx ]]; then
  wget https://dl.influxdata.com/influxdb/releases/influxdb2-client-${INFLUX_CLI_VERSION}-linux-amd64.tar.gz
  tar -xzf influxdb2-client-${INFLUX_CLI_VERSION}-linux-amd64.tar.gz
  sudo mv influxdb2-client-${INFLUX_CLI_VERSION}-2.2.0-linux-amd64/influx /usr/local/bin/
  rm -f influxdb2-client-${INFLUX_CLI_VERSION}-linux-amd64.tar.gz
  rm -f influxdb2-client-${INFLUX_CLI_VERSION}-linux-amd64
fi
