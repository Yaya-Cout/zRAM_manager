#!/usr/bin/env bash
# Get if user isn't root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit 1
fi
# Hard link zram_manager.py to /usr/bin/zram_manager
ln ./zram_manager.py /usr/bin/zram_manager
# Hard link zram_manager.service to /etc/systemd/system/zram_manager.service
ln ./zram_manager.service /etc/systemd/system/zram_manager.service
# Reload systemd
systemctl daemon-reload
# Enable zram_manager.service
systemctl enable zram_manager.service
# Start zram_manager.service
systemctl start zram_manager.service
echo "Installation complete"