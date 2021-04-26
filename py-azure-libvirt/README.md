# Libvirt Pulumi Example

- Deploys a VM in Azure that supports nested virtualization.
- Configures the VM so KVM/libvirt is running.
- Outputs a file named, `server.priv` that contains the ssh private key for connecting to the KVM server.
- (TODO) Deploys a VM on the KVM server using the Pulumi libvirt provider
  - https://github.com/pulumi/pulumi-libvirt

# Prerequisites

- ./venv/bin/pip install pulumi_libvirt

# Testing libvirt remotely on VM

- Store SSH private key that is output by the stack into a file, say, `server.priv`
- Install `virsh` or similar KVM/libvirt manager on some machine.
- Connect to remote KVM server using ssh-based connection URI: `qemu+ssh://kvmuser@KVM_SERVER_IP/system?keyfile=./server.priv`
- virsh example that assumes private key in file named `server.priv`
  - `virsh -c qemu+ssh://kvmuser@KVM_SERVER_IP/system?keyfile=./server.priv`
