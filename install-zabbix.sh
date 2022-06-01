#!/bin/bash
dnf update -y
yum install -y bash-completion yum-utils wget vim
source /etc/profile.d/bash_completion.sh

#setenforce 0
#sed -i 's/^SELINUX=.*/SELINUX=permissive/g' /etc/selinux/config
rpm -Uvh https://repo.zabbix.com/zabbix/6.0/rhel/8/x86_64/zabbix-release-6.0-1.el8.noarch.rpm
dnf clean all 
dnf install zabbix-server-pgsql zabbix-web-pgsql zabbix-nginx-conf zabbix-sql-scripts zabbix-selinux-policy zabbix-agent -y

dnf install @postgresql:13 -y

postgresql-setup initdb
systemctl enable postgresql
sed -i 's/ident/md5/g' /var/lib/pgsql/data/pg_hba.conf
systemctl restart postgresql
sudo -u postgres createuser --pwprompt zabbix
##Check Password input, sample Pa$$W0rd
sudo -u postgres createdb -O zabbix zabbix 
zcat /usr/share/doc/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix 
mv /etc/zabbix/zabbix_server.conf /etc/zabbix/zabbix_server.conf.bk
cat <<EOF > /etc/zabbix/zabbix_server.conf
LogFile=/var/log/zabbix/zabbix_server.log
LogFileSize=100
PidFile=/run/zabbix/zabbix_server.pid
SocketDir=/run/zabbix
DBName=zabbix
DBUser=zabbix
DBPassword=PassW0rd
StartPollers=25
StartPollersUnreachable=25
StartPingers=500
SNMPTrapperFile=/var/log/snmptrap/snmptrap.log
CacheSize=4G
HistoryCacheSize=512M
HistoryIndexCacheSize=512M
ValueCacheSize=1G
Timeout=4
LogSlowQueries=3000
StatsAllowedIP=127.0.0.1
AllowUnsupportedDBVersions=1
EOF

sed -i 's/\#//g' /etc/nginx/conf.d/zabbix.conf
systemctl restart zabbix-server zabbix-agent nginx php-fpm
systemctl enable zabbix-server zabbix-agent nginx php-fpm 

firewall-cmd --permanent --add-port=10050/tcp 
firewall-cmd --permanent --add-port=10051/tcp 
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --reload
echo 'change on file /etc/nginx/conf.d/zabbix.conf and access website with http://ip_address/setup.php'
echo 'Comment server in file /etc/nginx/nginx.conf'
echo 'systemctl restart zabbix-server zabbix-agent nginx php-fpm'