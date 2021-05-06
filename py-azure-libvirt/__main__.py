# Copyright 2016-2020, Pulumi Corporation.  All rights reserved.
# 
# Creates a KVM Host in Azure and deploys a VM in that KVM environment.
# The Libvirt provider is used with an SSH connection URI.
# Therefore, this project generates a local SSH private key file used to access the KVM host.

import pulumi as pulumi
from pulumi import Config, Output, ResourceOptions, export
import pulumi_libvirt as libvirt
import libvirt_host

# Get some stack-related config data
stackname = pulumi.get_stack()
config = Config()
basename = config.get("basename") or "libvirt-ex"
basename = f"{basename}-{stackname}"

# Create a KVM host
libvirt_server = libvirt_host.Server(basename)

# # Create a provider using the connection URI for the libvirt host
# libvirt_provider = libvirt.Provider(f"{basename}-libvirt",
#     uri=libvirt_server.libvirt_remote_uri
# )
# pulumi.export("provider", libvirt_provider)

# ### Build a VM on the KVM host.
# # Create a storage pool
# vm_pool = libvirt.Pool(f"{basename}-vm_pool",
#     args=libvirt.PoolArgs(type="dir", path=libvirt_server.vm_pool_dir), 
#     opts=ResourceOptions(provider=libvirt_provider)
# )
# export("libvirt pool name", vm_pool.name)

# # Create a small linux volume
# # Uses a tiny linux named cirros
# vm_vol = libvirt.Volume("linux",
#     pool=vm_pool.name,
#     source="http://download.cirros-cloud.net/0.5.2/cirros-0.5.2-x86_64-disk.img",
#     format="qcow2",
#     opts=ResourceOptions(provider=libvirt_provider)
# )
# export("libvirt volume name", vm_vol.name)

# # Create a VM using the volume created above.
# vm = libvirt.Domain(f"{basename}-vm",
#     memory=512,
#     vcpu=1,
#     disks=[libvirt.DomainDiskArgs(
#         volume_id=vm_vol.id
#     )],
#     network_interfaces=[libvirt.DomainNetworkInterfaceArgs(
#         network_name="default",
#         wait_for_lease=True,
#     )],
#     opts=ResourceOptions(provider=libvirt_provider)
# )
# export("libvirt VM name", vm.name)

test_cmd = Output.concat('echo virsh list | ssh -i ', libvirt_server.ssh_priv_key_file, ' ',libvirt_server.username,'@',libvirt_server.ip)
export("Check the libvirt VM on the KVM host", test_cmd)
