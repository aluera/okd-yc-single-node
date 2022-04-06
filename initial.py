#!/usr/bin/python3
import json
import os
import subprocess
import time
from datetime import datetime, timedelta

import yaml
from config import dns_zone_name, cluster_name, master_name, master_cpu, master_ram, master_type_disk, \
    size_disk_master_node, network_name, image_id, platform_id, scheduling_policy, zone, v4_cidr_blocks, pullSecret


def create_dirs():
    try:
        dirs_to_create = "bin", "okd-ignition", "secrets"
        for item in dirs_to_create:
            if os.path.isdir(item) != True:
                os.mkdir(item)
                print(f"Directory {item} - created!")
    except:
        exit("Error - create_dirs")


def get_yc_accounts():
    try:
        yc_service_account = subprocess.run("yc iam service-account list --format=json", shell=True,
                                            stderr=subprocess.PIPE,
                                            stdout=subprocess.PIPE)
        yc_service_account_data = json.loads(yc_service_account.stdout.decode("utf8"))
        for item in yc_service_account_data:
            if item['name'] == 'okd4-service-account':
                service_account_id = item['id']
                folder_id = item['folder_id']
                return service_account_id, folder_id
    except:
        exit("Error - get_yc_accounts")


def get_yc_accounts_key():
    try:
        if "key.json" in os.listdir():
            print("Key already exist!")
        else:
            os.system(
                "yc iam key create --service-account-name=okd4-service-account --algorithm='rsa-4096' -o key.json")
    except:
        exit("Error - get_yc_accounts_key")


def terraform_files(service_account_id: str, folder_id: str):
    if service_account_id != None and folder_id != None:
        def replace_data(data: list):
            for index, item in enumerate(data):
                if item.find("service_account_id") != -1:
                    if item.find("\"") != -1:
                        data[index] = f'  service_account_id = "{service_account_id}"\n'
                if item.find("folder_id") != -1:
                    if item.find("\"") != -1:
                        data[index] = f'  folder_id                = "{folder_id}"\n'
            return data

        with open("./terraform/main.tf", 'r', encoding='utf8') as main_tf:
            main_tf_data = main_tf.readlines()
        with open("./terraform/main.tf.without", 'r', encoding='utf8') as main_tf_without:
            main_tf_without_data = main_tf_without.readlines()
        with open("./terraform/main.tf", 'w', encoding='utf8') as main_tf:
            main_tf.writelines(replace_data(main_tf_data))
        with open("./terraform/main.tf.without", 'w', encoding='utf8') as main_tf_without:
            main_tf_without.writelines(replace_data(main_tf_without_data))
        with open("./terraform/terraform.tfvars", 'r', encoding='utf8') as tfvars:
            tfvars_data = tfvars.readlines()
        for index, item in enumerate(tfvars_data):
            if item.find('dns_zone_name') != -1:
                tfvars_data[index] = f'dns_zone_name         = "{dns_zone_name}"\n'
            if item.find('cluster_name') != -1:
                tfvars_data[index] = f'cluster_name          = "{cluster_name}"\n'
            if item.find('master_name') != -1:
                tfvars_data[index] = f'master_name           = "{master_name}"\n'
            if item.find('master_cpu') != -1:
                tfvars_data[index] = f'master_cpu            = {master_cpu}\n'
            if item.find('master_ram') != -1:
                tfvars_data[index] = f'master_ram            = {master_ram}\n'
            if item.find('master_type_disk') != -1:
                tfvars_data[index] = f'master_type_disk      = "{master_type_disk}"\n'
            if item.find('size_disk_master_node') != -1:
                tfvars_data[index] = f'size_disk_master_node = "{size_disk_master_node}"\n'
            if item.find('network_name') != -1:
                tfvars_data[index] = f'network_name          = "{network_name}"\n'
            if item.find('image_id') != -1:
                tfvars_data[index] = f'image_id              = "{image_id}"\n'
            if item.find('platform_id') != -1:
                tfvars_data[index] = f'platform_id           = "{platform_id}"\n'
            if item.find('scheduling_policy') != -1:
                tfvars_data[index] = f'scheduling_policy     = {scheduling_policy}\n'
            if item.find('zone') != -1:
                if item.find('dns_zone_name') == -1:
                    tfvars_data[index] = f'  zone           = "{zone}"\n'
            if item.find('v4_cidr_blocks') != -1:
                tfvars_data[index] = f'  v4_cidr_blocks = "{v4_cidr_blocks}"\n'
        with open("./terraform/terraform.tfvars", 'w', encoding='utf8') as tfvars:
            tfvars.writelines(tfvars_data)
        return True
    exit("Error - terraform_files")


def generate_ssh_keys():
    try:
        if os.path.isfile("./secrets/id_rsa") == True:
            print("ssh-key is exist!")
        else:
            ssh_keys_gen = os.system('ssh-keygen -f ./secrets/id_rsa -q -N ""')
            if ssh_keys_gen == 0:
                print("ssh-keys-done")
    except:
        exit("Error generating ssh key.")


def okd_config():
    try:
        with open("./okd-config/install-config.yaml") as conf:
            install_config = yaml.safe_load(conf)
        with open("./secrets/id_rsa.pub", 'r') as ssh_key:
            ssh_key_data = ssh_key.readline().rstrip()
        v4_cidr_ = v4_cidr_blocks.split("/")[0].split('.')
        v4_cidr_[2] = "0"
        v4_cidr_blocks_ = ".".join(v4_cidr_)
        install_config.update({'baseDomain': f'{dns_zone_name[0:-1]}'})
        install_config.update({'networking': {'clusterNetwork': [{'cidr': '10.128.0.0/14', 'hostPrefix': 23}],
                                              'machineNetwork': [{'cidr': f'{v4_cidr_blocks_}/16'}],
                                              'networkType': 'OVNKubernetes', 'serviceNetwork': ['172.30.0.0/16']}})
        install_config.update({'metadata': {'name': f'{cluster_name}'}})
        install_config.update({'pullSecret': pullSecret})
        install_config.update({'sshKey': f'{ssh_key_data}'})
        with open("./okd-config/install-config.yaml", "w") as conf:
            yaml.dump(install_config, conf)
    except:
        exit("Error - okd_config")


def generate_ignition_files():
    try:
        if len(os.listdir("./okd-config/")) <= 1:
            if os.system('cp ./okd-config/install-config.yaml ./okd-ignition/install-config.yaml') != 0:
                exit("Could not copy file.")
            if os.system('./bin/openshift-install create manifests --dir="./okd-ignition"') != 0:
                exit("Failed to create manifest.")
            if os.system('./bin/openshift-install create ignition-configs --dir="./okd-ignition"') != 0:
                exit("Failed to create ignition configs.")
            print('Generate okd config success')
        else:
            print("Okd ignitions already exist")
    except:
        exit("Error - generate_ignition_files")


def init():
    try:
        print("Create directories")
        create_dirs()
        print("Generate ssh keys")
        generate_ssh_keys()
        print("Terraform configs")
        terraform_files(*get_yc_accounts())
        print("Generate key")
        get_yc_accounts_key()
        print("Change Okd Config")
        okd_config()
        print("Generate okd ignitions")
        generate_ignition_files()
        print("Terraform init")
        os.system("""cd terraform/ && terraform init""")
        print("Initialization complete!")
    except:
        exit("Initialization Error")


def terraform_destroy_func():
    terraform_destroy = subprocess.run(
        ["terraform destroy -auto-approve"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if terraform_destroy.returncode != 0:
        print(terraform_destroy.stderr.decode('utf8'))
        exit("Something went wrong in apply!")
    else:
        print(terraform_destroy.stdout.decode('utf8'))
        print("Destroy success!")


def terraform_plan_func():
    terraform_plan = subprocess.run(
        ["terraform plan"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if terraform_plan.returncode != 0:
        print(terraform_plan.stderr.decode('utf8'))
        exit("Terraform plan error!")
    print(terraform_plan.stdout.decode("utf8"))


def terraform_apply_func():
    terraform_apply = subprocess.run(
        ["terraform apply -auto-approve"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if terraform_apply.returncode != 0:
        print(terraform_apply.stderr.decode("utf8"))
        terraform_destroy_func()
    print(terraform_apply.stdout.decode('utf8'))


def terraform_dir():
    if os.getcwd().split('/')[-1] != "terraform":
        os.chdir("./terraform")


def add_to_hosts(ip_address: str):
    with open("/etc/hosts") as file:
        hosts_file = file.readlines()
    index_to_del = set()
    for index, item in enumerate(hosts_file):
        if item.find(f"api.{cluster_name}.{dns_zone_name[0:-1]}") != -1 and item.find(ip_address) == -1:
            index_to_del.add(index)
        if item.find(f"api.{cluster_name}.{dns_zone_name[0:-1]}") != -1 and item.find(ip_address) != -1:
            index_to_del.add(index)
    if index_to_del != 0:
        for item in list(index_to_del)[::-1]:
            hosts_file.pop(item)
    hosts_file.append(f"{ip_address}\tapi.{cluster_name}.{dns_zone_name[0:-1]}\n")
    with open("temp_hosts.txt", 'w', encoding='utf8') as file:
        file.writelines(hosts_file)
    write_hosts = subprocess.run(["sudo su -c 'cat ./temp_hosts.txt > /etc/hosts'"],
                                 shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if write_hosts.returncode != 0:
        exit("Couldn't write to /etc/hosts")


def get_ip_address(node_name: str) -> str:
    try:
        with open("./terraform.tfstate") as file:
            json_data = json.load(file)
        ipv4_node = json_data["outputs"][f"{node_name}-ip-nat"]["value"]
        return ipv4_node
    except:
        terraform_dir()
        terraform_destroy_func()
        exit("Something went wrong!")


def bootstrapping():
    bootsrapping_ = os.system(
        "../bin/openshift-install --dir=../okd-ignition wait-for bootstrap-complete --log-level=debug")
    if bootsrapping_ != 0:
        retry_r = open("./terraform.tfvars", encoding='utf8').readlines()
        retry = json.loads(retry_r[-1].strip("#").replace('\'', '"'))
        if retry["retry_count"] < retry["max_retry_count"]:
            retry["retry_count"] += 1
            retry_r[-1] = f"#{retry}"
            open("./terraform.tfvars", 'w', encoding='utf8').writelines(retry_r)
            run_okd(True)
        else:
            retry_count_to_default()
            terraform_destroy_func()
            exit("OKD FAILED!")
    else:
        print("Bootstrapping successfully")


def retry_count_to_default():
    terraform_dir()
    retry_r = open("./terraform.tfvars", encoding='utf8').readlines()
    retry_r[-1] = "#{'retry_count': 0, 'max_retry_count': 3}"
    open("./terraform.tfvars", 'w', encoding='utf8').writelines(retry_r)


def run_okd(retry=False):
    if retry is True:
        terraform_dir()
        terraform_destroy_func()
    # Initial bootstap
    terraform_dir()
    terraform_plan_func()
    terraform_apply_func()
    ip_address_master = get_ip_address("master")
    add_to_hosts(ip_address_master)
    print(
        f"We are waiting for the bootstrap server to be pre-installed in 5 minutes: {(datetime.now() + timedelta(minutes=10)).strftime('%H:%M:%S')}")
    time.sleep(300)
    bootstrapping()
    # Delete bootstrap node and S3
    os.system("mv main.tf main.tf.save")
    os.system("mv main.tf.without main.tf")
    terraform_dir()
    terraform_plan_func()
    terraform_apply_func()
    # Output Resultats"
    password_okd = open("../okd-ignition/auth/kubeadmin-password", 'r', encoding='utf8').readline()
    print(f"""
--------Credentials to Access--------
ip_address_master: {ip_address_master}
login: kubeadmin
passowrd: {password_okd}
--------Login OKD--------
1. SSH to Master node <example>: ssh -i <use-id_rsa-in-secret-folder> core@{ip_address_master}
2. oc login localhost:6443  --username=kubeadmin --password={password_okd} --insecure-skip-tls-verify=false
Copy the SSH keys to your machine.
::::::ADD SOME ROWS TO HOSTS::::::
{ip_address_master}\tconsole-openshift-console.apps.{cluster_name}.{dns_zone_name[0:-1]}
{ip_address_master}\toauth-openshift.apps.{cluster_name}.{dns_zone_name[0:-1]}
""")
    # After install
    os.system("mv main.tf main.tf.without")
    os.system("mv main.tf.save main.tf")
    retry_count_to_default()


if __name__ == "__main__":
    init()
    run_okd()
