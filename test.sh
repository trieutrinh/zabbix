#!/bin/bash
set -xe
DB_TYPE="POSTGRES"
DB_VERSION=15
ZABBIX_VERSION="6.0"
ZABBIX_RELEASE="latest"
IP_A=$(ip a | grep inet.*brd | awk '{print $2}' | awk -F/ '{print $1}')

get_ostype() {
    local __return=$1
    DETECTION_STRING="/etc/*-release"
    if [[ $(ls ${DETECTION_STRING}) ]]; then
        OS=$( cat ${DETECTION_STRING} | grep ^ID= | awk -F= '{print $2}' | tr -cd [:alpha:])
        if [ $? -eq 0 ] && [ "$__return" ]; then
            eval $__return="${OS}"
            return 0
        fi
    else
        __return="Unknown"
        return 1;
    fi
}

get_osversion() {
    local __return=$1
    DETECTION_STRING="/etc/*-release"
    if [[ $(ls ${DETECTION_STRING}) ]]; then
        OSLEVEL=$(cat ${DETECTION_STRING} | grep VERSION_ID | sed 's/[^0-9]*\([0-9]*\).*/\1/')
        if [ $? -eq 0 ] && [ "$__return" ]; then
            eval $__return="${OSLEVEL}"
            return 0
        fi
    else
        __return="Unknown"
        return 1;
    fi
}
check_license() {
    local __return=$1
    LICENSE=$(sudo subscription-manager list | grep ^Status: | awk '{print $2}')
}
install_dependancies() {
    get_ostype OSTYPE
    echo "[INFO] Start OS Updates"
    if [ "$OSTYPE" == "ubuntu" ]; then
        sudo apt update -y
        sudo apt install -y  wget vim
    elif [ "$OSTYPE" == "centos" ]; then
        sudo yum update -y
        sudo yum install -y bash-completion yum-utils wget vim
    elif [ "$OSTYPE" == "rhel" ]; then
        check_license LIC_STATUS
        if [ "$LIC_STATUS" == "Not Subscribed" ]; then
            echo "[ERROR] Please Subscription RHEL"
            exit 1
        else
            sudo dnf update -y
            sudo dnf install -y yum-utils bash-completion wget vim
        fi
    else
        echo "[ERROR] No support OS ${OSTYPE}"
        exit 1
    fi
}
install_on_rhel() {

    get_ostype OSTYPE
    get_osversion OSLEVEL
    check_license LIC_STATUS
    if [ "$LIC_STATUS" == "Not Subscribed" ]; then
        echo "[ERROR] Please Subscription RHEL"
        exit 1
    else
        sudo dnf update -y
        sudo dnf install -y yum-utils bash-completion wget vim

        # rpm -Uvh https://repo.zabbix.com/zabbix/${ZABBIX_VERSION}/${OSTYPE}/${OSLEVEL}/x86_64/zabbix-release-${ZABBIX_RELEASE}.el${OSLEVEL}.noarch.rpm &
        rpm -Uvh https://repo.zabbix.com/zabbix/6.0/rhel/8/x86_64/zabbix-release-6.0-4.el8.noarch.rpm
        sleep 2
        # dnf clean all
        dnf install zabbix-server-pgsql zabbix-web-pgsql zabbix-nginx-conf zabbix-sql-scripts zabbix-selinux-policy zabbix-agent -y
        
        sudo dnf install @postgresql:${DB_VERSION} -y

    fi
}

install_db() {
    sudo mkdir -p /tmp
    sudo cd /tmp
    /usr/bin/postgresql-setup --initdb --unit postgresql

    sudo sed -i 's/ident/md5/g' /var/lib/pgsql/data/pg_hba.conf
    sudo systemctl enable postgresql
    sudo systemctl restart postgresql
    su postgres -c "psql -c \"CREATE USER zabbix with PASSWORD 'PassW0rd';\""
    
    sudo -u postgres createdb -O zabbix zabbix
    zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix 
    su postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE zabbix TO zabbix;\""
}

config_zabbix() {
    clear
    echo "Config zabbix Server"
    sleep 3

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
CacheSize=32M
HistoryCacheSize=32M
HistoryIndexCacheSize=32M
ValueCacheSize=32M
Timeout=4
LogSlowQueries=3000
StatsAllowedIP=127.0.0.1
AllowUnsupportedDBVersions=1
EOF
    
    sed -i 's/\#//g' /etc/nginx/conf.d/zabbix.conf
    sed  -i "s/listen          8080;/listen          80;/" /etc/nginx/conf.d/zabbix.conf
    sed -i '38,57 s/^/#/' /etc/nginx/nginx.conf
    sed -i "s/server_name     example.com;/server_name     localhost;/" /etc/nginx/conf.d/zabbix.conf
}

config_firewall() {
    yum install -y firewalld || echo "Firewalld installed"
    firewall-cmd --permanent --add-port=10050/tcp 
    firewall-cmd --permanent --add-port=10051/tcp 
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --reload 
}
reload_software() {

    systemctl restart zabbix-server zabbix-agent nginx php-fpm
    systemctl enable zabbix-server zabbix-agent nginx php-fpm
}
result() {
    clear
    echo "Access website with http://${IP_A}/setup.php for config Zabbix"
    echo "Information for config database: "
    echo "Username: zabbix"
    echo "Password: PassW0rd"
    echo "==================================="
    echo "Access Zabbix Dashboard:"
    echo "Username: Admin"
    echo "Password: zabbix"
}

install_on_rhel
install_db 
config_zabbix
reload_software
config_firewall
result

# Config default

# StartPollers=5
# StartIPMIPollers=0
# StartPollersUnreachable=1
# StartTrappers=5
# StartPingers=1
# StartDiscoverers=1
# HousekeepingFrequency=1
# CacheSize=32M
# StartDBSyncers=4
# HistoryCacheSize=16M
# TrendCacheSize=4M
# ValueCacheSize=8M
