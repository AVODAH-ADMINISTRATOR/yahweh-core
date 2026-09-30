#!/bin/bash
set -euo pipefail
echo "=== ELITE NODE INSPECTION — $(date -Is) — $(hostname) ==="
echo ""
echo "--- 0. PRIVILEGE & OS ---"
whoami; id; cat /etc/os-release | grep -E 'PRETTY|VERSION'; uname -r; uptime; echo ""

echo "--- 1. CPU / MEM / DISK / LOAD ---"
lscpu | grep -E 'Model name|CPU\(s\)|Thread|Core'; free -h; df -h / /public 2>/dev/null | head -10; vmstat 1 2 | tail -1; echo ""

echo "--- 2. NETWORK & DNS & GATEWAY ---"
ip -br a; ip r | head -10; ss -tlnp | head -30; cat /etc/resolv.conf | grep -v '^#'; ping -c1 1.1.1.1 2>&1 | tail -1; ping -c1 download.virtualbox.org 2>&1 | tail -1; echo ""

echo "--- 3. DOAS / SUDO / PERMISSIONS ---"
ls -l /etc/doas.conf /etc/sudoers 2>&1; cat /etc/doas.conf 2>/dev/null; groups; ls -ld /public/yahweh-core; echo ""

echo "--- 4. APT / REPO HEALTH ---"
apt-get check 2>&1 | tail -5; ls -l /etc/apt/sources.list.d/; cat /etc/apt/sources.list.d/virtualbox.list 2>/dev/null || echo "vbox repo: missing"; apt-cache policy tinyproxy virtualbox-7.0 2>&1 | head -40; echo ""

echo "--- 5. TINYPROXY SUBSYSTEM ---"
ls -lh /etc/tinyproxy/tinyproxy.conf /var/log/tinyproxy/tinyproxy.log 2>&1
cat /etc/tinyproxy/tinyproxy.conf 2>/dev/null | grep -v '^#' | grep -v '^$'
systemctl status tinyproxy --no-pager 2>&1 | head -40 || service tinyproxy status 2>&1 | head -20
ss -tlnp | grep tinyproxy; ps aux | grep tinyproxy | grep -v grep
echo "TEST PROXY:"; curl -x http://127.0.0.1:8888 -I http://example.com 2>&1 | head -5 || echo "proxy test: failed"
echo ""

echo "--- 6. VIRTUALBOX SUBSYSTEM ---"
VBoxManage --version 2>&1; VBoxManage list extpacks 2>&1 | head -20; VBoxManage list hostinfo 2>&1 | head -20
lsmod | grep vbox; systemctl status vboxdrv 2>&1 | head -10 || modinfo vboxdrv 2>&1 | head -5
ls -lh /usr/share/keyrings/oracle-virtualbox* 2>&1; echo ""

echo "--- 7. KERNEL MODULES & DKMS ---"
dkms status 2>&1 | head -30; dmesg | grep -i -E 'vbox|tinyproxy|error|fail' | tail -20; echo ""

echo "--- 8. FILESYSTEM INTEGRITY & DEPLOY SCRIPTS ---"
cd /public/yahweh-core; pwd; ls -lh *.sh 2>&1; bash -n ./tinyproxy_deploy.sh && echo tinyproxy_deploy:syntax:ok || echo tinyproxy_deploy:syntax:FAIL; bash -n ./vbox_deploy.sh && echo vbox_deploy:syntax:ok || echo vbox_deploy:syntax:FAIL; git status --short; echo ""

echo "--- 9. SECURITY POSTURE ---"
cat /etc/tinyproxy/tinyproxy.conf 2>/dev/null | grep -E 'Listen|Allow' | head -10
echo "Open ports:"; ss -tlnp | grep -v 127.0.0.1 | head -20
echo "UFW:"; ufw status 2>&1 | head -20 || iptables -L -n 2>&1 | head -20
echo ""

echo "--- 10. FINAL ELITE SCORE ---"
systemctl is-active tinyproxy 2>/dev/null && T=1 || T=0
VBoxManage --version >/dev/null 2>&1 && V=1 || V=0
[ -f /etc/doas.conf ] && D=1 || D=0
[ -f /etc/tinyproxy/tinyproxy.conf ] && C=1 || C=0
echo "TINYPROXY_ACTIVE=$T VBOX_INSTALLED=$V DOAS_CONF=$D CONF_EXISTS=$C"
[ $T -eq 1 ] && [ $V -eq 1 ] && [ $D -eq 1 ] && [ $C -eq 1 ] && echo "ELITE STATUS: NODE PROVISIONED OK — Integrated Avodah LLC — Lawrence, KS" || echo "ELITE STATUS: NEEDS REMEDIATION — check 0-9 above"
