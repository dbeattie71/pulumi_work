# Copyright 2016-2020, Pulumi Corporation.  All rights reserved.

import base64
import pulumi as pulumi
from pulumi import Config, Output, ResourceOptions, export
import pulumi_azure_native.compute as compute
import pulumi_azure_native.network as network
import pulumi_azure_native.resources as resources
import pulumi_tls as tls
import pulumi_libvirt as libvirt
import os as os

stackname = pulumi.get_stack()
config = Config()
username = config.get("username") or "kvmuser"
basename = config.get("basename") or "kvm-server"
basename = f"{basename}-{stackname}"

# SSH key for accessing the Azure VM that is going to be the KVM host.
ssh_key = tls.PrivateKey("ssh-key", algorithm="RSA", rsa_bits=4096)

# Resource group, etc for the kvm-server
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

# Script to configure the kvm service on the kvm host
init_script = f"""#!/bin/bash

# Install KVM
sudo apt update
sudo apt-get -y install qemu-kvm libvirt-bin 
sudo usermod -a -G libvirtd {username}
# hack to account for this bug: https://bugs.launchpad.net/ubuntu/+source/libvirt/+bug/1677398
sudo echo security_driver = \\"none\\" >> /etc/libvirt/qemu.conf
sudo systemctl restart libvirt-bin
"""

# unnecessary stuff(?) for custom data script
# sudo apt-get -y install virtinst bridge-utils cpu-checker
# Set up virsh pool
#VMS_DIR={vms_dir}
#VMS_STORE={vms_store}
#mkdir $VMS_DIR
#sudo virsh pool-define-as $VMS_STORE --type dir --target $VMS_DIR
#sudo virsh pool-start $VMS_STORE
#sudo virsh pool-autostart $VMS_STORE

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
        ),
        image_reference=compute.ImageReferenceArgs(
            publisher="canonical",
            offer="UbuntuServer",
            #sku="16.04-LTS",
            sku="18.04-LTS",
            version="latest",
        ),
    ))

combined_output = Output.all(vm.id, public_ip.name, resource_group.name)
public_ip_addr = combined_output.apply(
    lambda lst: network.get_public_ip_address(
        public_ip_address_name=lst[1], 
        resource_group_name=lst[2]))
export("KVM server IP", public_ip_addr.ip_address)


# Generate the private key file for use by the provider
def write_key_file(priv_key, key_file):
    if (os.path.exists(key_file)):
        os.chmod(key_file, 0o666)
    f = open(key_file, "w")
    f.write(priv_key)
    f.close()
    os.chmod(key_file, 0o400)

key_file=f"{basename}_server.priv"
ssh_key.private_key_pem.apply(
    lambda priv_key: write_key_file(priv_key, key_file)
)
export("KVM server ssh private key file ", key_file)

# See https://libvirt.org/uri.html#URI_remote for details on the remote URI options
libvirt_remote_uri = Output.concat("qemu+ssh://",username,"@",public_ip_addr.ip_address,"/system?keyfile=./",key_file,"&socket=/var/run/libvirt/libvirt-sock&no_verify=1")
libvirt_provider = libvirt.Provider(f"{basename}-libvirt",
    uri=libvirt_remote_uri
)

vm_pool_dir = f"/home/{username}/vms"  # the "vm pool" will be under the user created on the KVM host
vm_pool = libvirt.Pool(f"{basename}-vm_pool",
    args=libvirt.PoolArgs(type="dir", path=vm_pool_dir), 
    opts=ResourceOptions(provider=libvirt_provider)
)
export("libvirt pool name", vm_pool.name)

# Create a small linux volume
vm_vol = libvirt.Volume("linux",
    pool=vm_pool.name,
    source="http://download.cirros-cloud.net/0.5.2/cirros-0.5.2-x86_64-disk.img",
    format="qcow2",
    opts=ResourceOptions(provider=libvirt_provider)
)
export("libvirt volume name", vm_vol.name)

# Create a VM using the volume created above.
vm = libvirt.Domain(f"{basename}-vm",
    memory=512,
    vcpu=1,
    disks=[libvirt.DomainDiskArgs(
        volume_id=vm_vol.id
    )],
    network_interfaces=[libvirt.DomainNetworkInterfaceArgs(
        network_name="default",
        wait_for_lease=True,
    )],
    opts=ResourceOptions(provider=libvirt_provider)
)
export("libvirt VM name", vm.name)

test_cmd = Output.concat('echo virsh list', vm.name, ' | ssh -i ', key_file, ' ',username,'@',public_ip_addr.ip_address)
test_cmd.apply(lambda cmd: os.system(cmd))
