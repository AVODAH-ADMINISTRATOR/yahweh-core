#!/bin/bash
while true; do
  if! pgrep -f GO_BINARY_FINAL >/dev/null; then
    cd /root/yahweh-core; nohup bash GO_BINARY_FINAL.sh > /tmp/binary.log 2>&1 &
    echo "$(date -Is) WATCHDOG BINARY FINAL RESURRECTION b08a2817 FULL ASSEMBLY DEPTH GO" >>.audit_archive/light/flow.log
  fi
  sleep 15
done
