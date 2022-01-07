#!/usr/bin/env bash

set -o nounset
set -o errexit
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR
set -o errtrace
set -o pipefail
IFS=$'\n\t'


if type plantuml > /dev/null 2>&1 ; then
cat <<- EOS > /tmp/plantuml.service
[Unit]
Description=PlantUML
After=network.target

[Service]
Type=simple
ExecStart=/home/linuxbrew/.linuxbrew/bin/plantuml -picoweb:8989

[Install]
WantedBy=multi-user.target
EOS
sudo mkdir -p /usr/local/lib/systemd/system
sudo mv /tmp/plantuml.service /etc/systemd/system/plantuml.service
sudo chown root:root /etc/systemd/system/plantuml.service
sudo systemctl daemon-reload
sudo systemctl start plantuml.service

fi
