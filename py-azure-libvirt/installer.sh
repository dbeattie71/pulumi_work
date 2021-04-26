
# INSTALL KVM
sudo apt update
sudo apt-get -y install qemu-kvm libvirt-bin virtinst bridge-utils cpu-checker

# Set up virsh pool
VMS_DIR=~/vms
VMS_STORE=vms-store
mkdir $VMS_DIR
sudo virsh pool-define-as ${VMS_STORE} --type dir --target ${VMS_DIR}
sudo virsh pool-start ${VMS_STORE}
sudo virsh pool-autostart ${VMS_STORE}
