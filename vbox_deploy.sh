#!/bin/bash
set -euo pipefail
apt-get update -qq
apt-get install -y -qq curl gnupg lsb-release build-essential dkms linux-headers-$(uname -r)
curl -fsSL https://www.virtualbox.org/download/oracle_vbox_2016.asc | gpg --dearmor -o /usr/share/keyrings/oracle-virtualbox-2016.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/oracle-virtualbox-2016.gpg] https://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" > /etc/apt/sources.list.d/virtualbox.list
apt-get update -qq
echo "virtualbox-ext-pack virtualbox-ext-pack/license select true" | debconf-set-selections
apt-get install -y -qq virtualbox-7.0 virtualbox-ext-pack
VBoxManage --version && echo vbox:ok
