# Copyright 2016-2020, Pulumi Corporation.  All rights reserved.

import base64
from pulumi import Config, Output, ResourceOptions, export
import pulumi_azure_native.compute as compute
import pulumi_azure_native.network as network
import pulumi_azure_native.resources as resources
import pulumi_tls as tls
import pulumi_libvirt as libvirt
import os as os
import time

config = Config()
username = config.get("username") or "kvmuser"
basename = config.get("basename") or "kvm-server"

ssh_key = tls.PrivateKey("ssh-key", algorithm="RSA", rsa_bits=4096)

resource_group = resources.ResourceGroup(f"{basename}-rg")

net = network.VirtualNetwork(
    f"{basename}-net",
    resource_group_name=resource_group.name,
    address_space=network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"],
    ),
    subnets=[network.SubnetArgs(
        name="default",
        address_prefix="10.0.1.0/24",
    )])

public_ip = network.PublicIPAddress(
    f"{basename}-ip",
    resource_group_name=resource_group.name,
    public_ip_allocation_method=network.IPAllocationMethod.DYNAMIC)

network_iface = network.NetworkInterface(
    f"{basename}-nic",
    resource_group_name=resource_group.name,
    ip_configurations=[network.NetworkInterfaceIPConfigurationArgs(
        name="serveripcfg",
        subnet=network.SubnetArgs(id=net.subnets[0].id),
        private_ip_allocation_method=network.IPAllocationMethod.DYNAMIC,
        public_ip_address=network.PublicIPAddressArgs(id=public_ip.id),
    )])

# Script to configure kvm that is run on the server
vms_dir = f"/home/{username}/vms"
vms_store = "vms-store"
init_script = f"""#!/bin/bash

# Install KVM
sudo apt update
sudo apt-get -y install qemu-kvm libvirt-bin virtinst bridge-utils cpu-checker

# Set up virsh pool
VMS_DIR={vms_dir}
VMS_STORE={vms_store}
mkdir $VMS_DIR
sudo virsh pool-define-as $VMS_STORE --type dir --target $VMS_DIR
sudo virsh pool-start $VMS_STORE
sudo virsh pool-autostart $VMS_STORE"""
# sudo usermod -a -G libvirtd kvmuser"""

vm = compute.VirtualMachine(
    f"{basename}-vm",
    resource_group_name=resource_group.name,
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(id=network_iface.id),
        ],
    ),
    hardware_profile=compute.HardwareProfileArgs(
        vm_size=compute.VirtualMachineSizeTypes.STANDARD_D4S_V3
    ),
    os_profile=compute.OSProfileArgs(
        computer_name="hostname",
        admin_username=username,
        custom_data=base64.b64encode(init_script.encode("ascii")).decode("ascii"),
        linux_configuration=compute.LinuxConfigurationArgs(
            ssh=compute.SshConfigurationArgs(
                public_keys=[compute.SshPublicKeyArgs(
                    key_data=ssh_key.public_key_openssh,
                    path=f'/home/{username}/.ssh/authorized_keys'
                )]
            )
        )
    ),
    storage_profile=compute.StorageProfileArgs(
        os_disk=compute.OSDiskArgs(
            create_option=compute.DiskCreateOptionTypes.FROM_IMAGE,
            name="myosdisk1",
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher="canonical",
            offer="UbuntuServer",
            sku="16.04-LTS",
            version="latest",
        ),
    ))

combined_output = Output.all(vm.id, public_ip.name, resource_group.name)
public_ip_addr = combined_output.apply(
    lambda lst: network.get_public_ip_address(
        public_ip_address_name=lst[1], 
        resource_group_name=lst[2]))
export("public_ip", public_ip_addr.ip_address)


# def write_key_file(priv_key, key_file):
#     os.chmod(key_file, 0o666)
#     f = open(key_file, "a")
#     f.write(priv_key)
#     f.close()
#     os.chmod(key_file, 0o400)

key_file="server.priv"
# ssh_key.private_key_pem.apply(
#     lambda priv_key: write_key_file(priv_key, key_file)
# )
export("ssh_private_key_file", key_file)

libvirt_provider = libvirt.Provider(f"{basename}-libvirt",
    uri=Output.concat("qemu+ssh://",username,"@",public_ip_addr.ip_address,"/system?keyfile=./",key_file,"&socket=/var/run/libvirt/libvirt-sock")
)
export("provider", libvirt_provider)

import pulumi
import pulumi_libvirt as libvirt

# A pool for all cluster volumes
opensuse_leap = libvirt.Volume("tinycore-11.1",
    pool="vms-store",
    source="http://downloads.sourceforge.net/project/gns-3/Qemu%20Appliances/linux-tinycore-11.1.qcow2",
    opts=ResourceOptions(provider=libvirt_provider)
)

# default = libvirt.Domain(f"{basename}libvirtdomain",
#     opts=ResourceOptions(provider=libvirt_provider)
# )


# opensuse_leap = libvirt.Volume(f"{basename}-suse-vol", 
#     source="http://download.opensuse.org/repositories/Cloud:/Images:/Leap_42.1/images/openSUSE-Leap-42.1-OpenStack.x86_64.qcow2",
#     opts=ResourceOptions(provider=libvirt_provider)
# )
