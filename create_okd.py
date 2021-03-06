#!/usr/bin/python3
import argparse
import datetime
import json
import os
import shutil
import subprocess
import time

import hcl
import requests
import yaml

# Default dir
default_dir = ""
tf_dir = ""
# Global
bucket_name = f"bucket-bootstrap-okd4-{int(time.time())}"
with open(f"{default_dir}/terraform-conf.tfvars", "r", encoding='utf8') as tfvars_conf:
    tfvars_conf = hcl.load(tfvars_conf)
cluster_name = tfvars_conf.get("cluster_name")
dns_zone_name = tfvars_conf.get("dns_zone_name")
v4_cidr_blocks = tfvars_conf.get("subnets").get("v4_cidr_blocks")


def clear_to_default():
    if os.path.exists(f"{default_dir}/okd-ignition/"):
        shutil.rmtree(f"{default_dir}/okd-ignition/")
    if os.path.exists(f"{default_dir}/okd-ignition/"):
        shutil.rmtree(f"{default_dir}/okd-ignition/")
    if os.path.exists(f"{default_dir}/terraform/.terraform"):
        shutil.rmtree(f"{default_dir}/terraform/.terraform")
    if os.path.exists(f"{default_dir}/terraform/.terraform.lock.hcl"):
        os.remove(f"{default_dir}/terraform/.terraform.lock.hcl")
    if os.path.exists(f"{default_dir}/terraform/terraform.tfstate"):
        os.remove(f"{default_dir}/terraform/terraform.tfstate")
    if os.path.exists(f"{default_dir}/terraform/terraform.tfstate.backup"):
        os.remove(f"{default_dir}/terraform/terraform.tfstate.backup")
    if os.path.exists(f"{default_dir}/terraform/temp_hosts.txt"):
        os.remove(f"{default_dir}/terraform/temp_hosts.txt")
    print("Clear: Success")


def is_default() -> None:
    try:
        if 'okd-ignition' in os.listdir():
            clear_to_default()
        else:
            print("Check is default: Success")
    except Exception as exc:
        print(exc)
        exit("Clear all to default: Failed")


def create_dir() -> None:
    try:
        dirs_to_create = "okd-ignition"
        if not os.path.isdir(f"{default_dir}/okd-ignition"):
            os.mkdir(f"{default_dir}/{dirs_to_create}")
            print(f"Directory {dirs_to_create} create: Success")
    except Exception as exc:
        print(exc)
        exit("Create directory: Failed")


def request_token_iam() -> tuple:
    def request_meta(meta_data_url):
        metadata_flavor = {'Metadata-Flavor': 'Google'}
        data = requests.get(meta_data_url, headers=metadata_flavor)
        if data.status_code == 200:
            return data.text
        else:
            exit("Get MetaData: Failed")

    metadata_token = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token/"
    metadata_folderid = "http://169.254.169.254/computeMetadata/v1/yandex/folder-id/"
    metadata_sshkey = "http://169.254.169.254/computeMetadata/v1/instance/attributes/ssh-keys/"
    try:
        iam_token = json.loads(request_meta(
            metadata_token)).get("access_token")
        iam_folder_id = request_meta(metadata_folderid)
        iam_ssh_key = request_meta(metadata_sshkey).split(":")[-1]
        iam_service_account_id = json.loads(subprocess.run(
            ["yc compute instance get --format=json `curl -s -H Metadata-Flavor:Google "
             "169.254.169.254/computeMetadata/v1/instance/id`"],
            shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).
                                            stdout.decode('utf8')).get("service_account_id")
        return iam_token, iam_folder_id, iam_service_account_id, iam_ssh_key
    except Exception as exc:
        print(exc)
        exit("IAM DATA: Failed")


def tf_main(iam_token: str, iam_folder_id: str, iam_service_account_id: str) -> None:
    def update_iam(data: list) -> list:
        for index, item in enumerate(data):
            if item.find("service_account_id") != -1:
                if item.find("\"") != -1:
                    data[index] = f'  service_account_id = "{iam_service_account_id}"\n'
            if item.find("folder_id") != -1:
                if item.find("\"") != -1:
                    data[index] = f'  folder_id = "{iam_folder_id}"\n'
            if item.find("bucket        = ") != -1:
                data[index] = f'  bucket        = "{bucket_name}"\n'
            if item.find("token") != -1:
                data[index] = f'  token     = "{iam_token}"\n'
        return data

    try:
        with open(f"{default_dir}/terraform/main.tf", 'r', encoding='utf8') as main_tf:
            main_tf_data = main_tf.readlines()
        with open(f"{default_dir}/terraform/main.tf.without", 'r', encoding='utf8') as main_tf_without:
            main_tf_without_data = main_tf_without.readlines()
        with open(f"{default_dir}/terraform/main.tf", 'w', encoding='utf8') as main_tf:
            main_tf.writelines(update_iam(main_tf_data))
        with open(f"{default_dir}/terraform/main.tf.without", 'w', encoding='utf8') as main_tf_without:
            main_tf_without.writelines(update_iam(main_tf_without_data))
    except Exception as exc:
        print(exc)
        exit("Terraform config change: Failed")


def okd_pull_secret() -> str:
    with open(f'{default_dir}/okd-pull-secret.txt', 'r', encoding='utf8') as pullSecret_f:
        pullSecret_f = pullSecret_f.readlines()
    for item in pullSecret_f:
        try:
            pullSecret = json.loads(item)
            break
        except:
            pullSecret = None
    if pullSecret is not None:
        return str(pullSecret).replace("'", '"')
    else:
        exit("Get pullSecret in okd-pull-secret.txt: Failed")


def okd_config(ssh_key_data: str) -> None:
    try:
        with open(f"{default_dir}/okd-config/install-config.yaml") as conf:
            install_config = yaml.safe_load(conf)
        pullSecret = okd_pull_secret()
        v4_cidr_ = v4_cidr_blocks.split("/")[0].split('.')
        v4_cidr_[2] = "0"
        v4_cidr_blocks_ = ".".join(v4_cidr_)
        ssh_key_data = ssh_key_data.replace('\n', '')
        install_config.update({'baseDomain': f'{dns_zone_name[0:-1]}'})
        install_config.update({'networking': {'clusterNetwork': [{'cidr': '10.128.0.0/14', 'hostPrefix': 23}],
                                              'machineNetwork': [{'cidr': f'{v4_cidr_blocks_}/16'}],
                                              'networkType': 'OVNKubernetes', 'serviceNetwork': ['172.30.0.0/16']}})
        install_config.update({'metadata': {'name': f'{cluster_name}'}})
        install_config.update({'pullSecret': pullSecret})
        install_config.update({'sshKey': f'{ssh_key_data}'})
        with open(f"{default_dir}/okd-config/install-config.yaml", "w") as conf:
            yaml.dump(install_config, conf)
    except Exception as exc:
        print(exc)
        exit("OKD config: Failed")


def generate_ignition_files() -> None:
    try:
        if len(os.listdir(f"{default_dir}/okd-config/")) <= 1:
            if os.system(
                    f'cp {default_dir}/okd-config/install-config.yaml {default_dir}/okd-ignition/install-config.yaml') != 0:
                exit("Copy install-config.yaml file: Failed")
            if os.system(
                    f'{default_dir}/bin/openshift-install create manifests --dir="{default_dir}/okd-ignition"') != 0:
                exit("Create manifest: Failed")
            if os.system(
                    f'{default_dir}/bin/openshift-install create ignition-configs --dir="{default_dir}/okd-ignition"') != 0:
                exit("Failed to create ignition configs")
            print('Generate OKD config: Success')
        else:
            print("OKD ignitions already exist")
    except Exception as exc:
        print(exc)
        exit("Creating OKD Ignitions: Failed")


def mv_config() -> None:
    if os.system(f"cp {default_dir}/terraform-conf.tfvars {tf_dir}/terraform.tfvars") != 0:
        exit("Copy terraform-conf.tfvars: Failed")


def terraform_init_func() -> None:
    try:
        if os.system(f"cd {tf_dir} && terraform init") != 0:
            exit("Terraform init: Failed")
    except Exception as exc:
        print(exc)
        exit("Terraform init: Failed")


def terraform_destroy_func() -> None:
    terraform_dir()
    terraform_destroy = subprocess.run(
        ["terraform destroy -auto-approve"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if terraform_destroy.returncode != 0:
        print(terraform_destroy.stderr.decode('utf8'))
        exit("Terraform destroy: Failed")
    else:
        print(terraform_destroy.stdout.decode('utf8'))
        print("Terraform destroy: Success")


def terraform_plan_func() -> None:
    terraform_dir()
    terraform_plan = subprocess.run(
        ["terraform plan"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if terraform_plan.returncode != 0:
        print(terraform_plan.stderr.decode('utf8'))
        exit("Terraform plan: Failed")
    print(terraform_plan.stdout.decode("utf8"))


def terraform_apply_func() -> None:
    terraform_dir()
    terraform_apply = subprocess.run(
        ["terraform apply -auto-approve"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if terraform_apply.returncode != 0:
        print(terraform_apply.stderr.decode("utf8"))
        terraform_destroy_func()
    print(terraform_apply.stdout.decode('utf8'))


def terraform_dir() -> None:
    if os.getcwd().split('/')[-1] != "terraform":
        os.chdir(f"{tf_dir}")


def add_to_hosts(ip_address: str) -> None:
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
    hosts_file.append(
        f"{ip_address}\tapi.{cluster_name}.{dns_zone_name[0:-1]}\n")
    with open("temp_hosts.txt", 'w', encoding='utf8') as file:
        file.writelines(hosts_file)
    write_hosts = subprocess.run([f"sudo su -c 'cat {tf_dir}/temp_hosts.txt > /etc/hosts'"],
                                 shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if write_hosts.returncode != 0:
        exit("Recording temp_hosts.txt in /etc/hosts: Failed")


def get_ip_address(node_name: str) -> str:
    try:
        with open(f"{tf_dir}/terraform.tfstate") as file:
            json_data = json.load(file)
        ipv4_node = json_data["outputs"][f"{node_name}-ip-nat"]["value"]
        return ipv4_node
    except Exception as exc:
        print(exc)
        terraform_destroy_func()
        exit("Get ip address in terraform.tfstate: Failed")


def init() -> None:
    try:
        is_default()
        iam_token, iam_folder_id, iam_service_account_id, iam_ssh_key = request_token_iam()
        print("IAM: Success")
        mv_config()
        print("Copy user config: Success")
        create_dir()
        print("Create directory: Success")
        okd_config(iam_ssh_key)
        print("OKD config: Success")
        tf_main(iam_token, iam_folder_id, iam_service_account_id)
        print("Modify configs: Success")
        generate_ignition_files()
        print("OKD ignition: Success")
        terraform_init_func()
        print("Terraform init: Success")
        print("Initialization: Success")
    except Exception as exc:
        print(exc)
        exit("Initialization: Error")


def initial_bootstap(is_rety=False) -> None:
    if is_rety is True:
        terraform_destroy_func()
    wait_time = 10
    terraform_plan_func()
    terraform_apply_func()
    ip_address_master = get_ip_address("master")
    add_to_hosts(ip_address_master)
    print(
        f"We are waiting for the bootstrap server to be pre-installed in {wait_time} "
        f"minutes: {(datetime.datetime.now() + datetime.timedelta(minutes=wait_time)).strftime('%H:%M:%S')}")
    time.sleep(wait_time * 60)


def bootstrapping(retry=2) -> None:
    bootstrapping_ = os.system(
        f"{default_dir}/bin/openshift-install --dir={default_dir}/okd-ignition wait-for bootstrap-complete --log-level=debug")
    if bootstrapping_ != 0:
        if retry != 0:
            retry -= 1
            initial_bootstap(True)
            bootstrapping(retry)
        else:
            exit("Retry count over: Failed")
    else:
        print("Bootstrapping node: Success")


def install() -> None:
    initial_bootstap()
    bootstrapping()
    os.system("mv main.tf main.tf.save")
    os.system("mv main.tf.without main.tf")
    terraform_plan_func()
    terraform_apply_func()
    password_okd = open(f"{default_dir}/okd-ignition/auth/kubeadmin-password",
                        'r', encoding='utf8').readline()
    ip_address_master = get_ip_address("master")
    print(f"""
--------Credentials to Access--------
ip_address_master: {ip_address_master}
login: kubeadmin
password: {password_okd}
--------Login OKD--------
1. SSH to Master node:
User: core@{ip_address_master}
2. oc login localhost:6443  --username=kubeadmin --password={password_okd} --insecure-skip-tls-verify=false
:::::Console OKD::::::
{ip_address_master}\tconsole-openshift-console.apps.{cluster_name}.{dns_zone_name[0:-1]}
{ip_address_master}\toauth-openshift.apps.{cluster_name}.{dns_zone_name[0:-1]}
""")
    os.system("mv main.tf main.tf.without")
    os.system("mv main.tf.save main.tf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flip a switch by setting a flag")
    parser.add_argument('-install', action='store_true')
    parser.add_argument('-delete', action='store_true')
    parser.add_argument('-clear-to-default', action='store_true')
    args = parser.parse_args()
    if args.install:
        print("Intall OKD")
        init()
        install()
    if args.delete:
        print("Delete created instances")
        terraform_destroy_func()
    if args.clear_to_default:
        print("Clear data to default")
        clear_to_default()
