#!/bin/sh
echo "Chose okd vesrsion more read: https://github.com/openshift/okd/releases/"
echo "1. OKD 4.9"
echo "2. OKD 4.10"
echo "3. Your version"
read -p "Your choose: " choose
REGEX_OKD_VERSION=".okd-"
if [[ $choose == 1 ]]; then
    okd_version="4.9.0-0.okd-2022-02-12-140851"
    echo "Download OKD version - $okd_version"
    elif [[ $choose == 2 ]]; then
    okd_version="4.10.0-0.okd-2022-03-07-131213"
    echo "Download OKD version - $okd_version"
    elif [[ $choose == 3 ]];then
    read -p "Input your version: " okd_version
    if [[ $okd_version =~ $REGEX_OKD_VERSION ]]; then
        echo "Download OKD version - $okd_version"
    else
        echo " DOES NOT MATCH REGEX_OKD_VERSION $okd"
        break
    fi
else
    break
fi

FILE=./bin/openshift-install
if [ -d "bin" ]; then
    echo "Downloading OKD openshift-install..."
    wget "https://github.com/openshift/okd/releases/download/$okd_version/openshift-install-linux-$okd_version.tar.gz"
    echo "Extracting openshift-install..."
    tar xzf openshift-install-linux-$okd_version.tar.gz --directory ./bin
    echo "Removing tar..."
    rm openshift-install-linux-$okd_version.tar.gz
    echo "Giving +x"
    chmod +x ./bin/openshift-install
else
    mkdir bin
    echo "Downloading OKD openshift-install..."
    wget "https://github.com/openshift/okd/releases/download/$okd_version/openshift-install-linux-$okd_version.tar.gz"
    echo "Extracting openshift-install..."
    tar xzf openshift-install-linux-$okd_version.tar.gz --directory ./bin
    echo "Removing tar..."
    rm openshift-install-linux-$okd_version.tar.gz
    echo "Giving +x"
    chmod +x ./bin/openshift-install
fi

FILE=./bin/oc
if [ -d "bin" ]; then
    echo "Downloading OKD OC..."
    wget "https://github.com/openshift/okd/releases/download/$okd_version/openshift-client-linux-$okd_version.tar.gz"
    echo "Extracting openshift-install..."
    tar xzf openshift-client-linux-$okd_version.tar.gz --directory ./bin
    echo "Removing tar..."
    rm openshift-client-linux-$okd_version.tar.gz
    echo "Giving +x"
    chmod +x ./bin/oc
else
    mkdir bin
    echo "Downloading OKD OC..."
    wget "https://github.com/openshift/okd/releases/download/$okd_version/openshift-client-linux-$okd_version.tar.gz"
    echo "Extracting openshift-install..."
    tar xzf openshift-client-linux-$okd_version.tar.gz --directory ./bin
    echo "Removing tar..."
    rm openshift-client-linux-$okd_version.tar.gz
    echo "Giving +x"
    chmod +x ./bin/oc
fi
