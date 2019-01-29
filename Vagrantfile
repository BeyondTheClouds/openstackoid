# -*- mode: ruby -*-
# vi: set ft=ruby :
#
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative
#
# This Vagrant file deploys two *independent* OpenStack instances. And
# then configures them so they can interpret the `--scope` for
# collaboration between services.
#
# - Deploy OpenStack solely
#   : vagrant up --provision-with devstack
# - Configure HAProxy and the scope
#   : vagrant provision --provision-with os-scope
#

# Configuration of OpenStack instances
os_instances = [
  {
    :name => "InstanceOne",
    :ip => "192.168.141.245",
    :ssh => 2141
  },
  {
    :name => "InstanceTwo",
    :ip => "192.168.142.245",
    :ssh => 2142
  }
]

Vagrant.configure(2) do |config|
  config.vm.box = "bento/ubuntu-16.04"

  # Configuration for VirtualBox
  config.vm.provider :virtualbox do |vb, override|
    vb.cpus = 6
    vb.memory = 6144
    override.vm.synced_folder "./", "/vagrant",
                              owner: "vagrant",
                              group: "vagrant"
  end

  # Start OpenStacks
  os_instances.each do |os_instance|
    make_os config, os_instance, os_instances
  end
end

# ------------------------------------------------------------------------
# Utils

def run_ansible(vm, name, vars)
  vm.provision name, type: :ansible_local do |ansible|
    ansible.install_mode = "pip"
    ansible.version = "2.6.11"
    ansible.compatibility_mode = "2.0"
    ansible.playbook = "playbooks/#{name}.yml"
    ansible.extra_vars = vars
    # ansible.verbose = "-vvvv"
  end
end

# Make a new *independant* OpenStack instance.
#
# The creation of the OpenStack instance goes through two provisioning
# phase:
#
# 1. --provision-with devstack :: Deploys OS with Devstack
# 2. --provision-with os-scope :: Deploys HAProxy and set the scope
#    interpretation.
def make_os(config, os_instance, os_instances)
  config.vm.define os_instance[:name] do |os|
    # exit!
    os.vm.hostname = os_instance[:name]
    os.vm.network :private_network, ip: os_instance[:ip], auto_config: true
    os.vm.network :forwarded_port, guest: 22, host: os_instance[:ssh], id: "ssh"
    #os.vm.network :forwarded_port, guest: 80, host: 8881

    # Setup and Install devstack
    run_ansible(os.vm, "devstack", {
        :os_name => os_instance[:name],
        :os_ip => os_instance[:ip]
      })

    # Interpret the scope
    run_ansible(os.vm, "os-scope", {
      :current_instance => os_instance,
      :os_instances => os_instances
    })
  end
end
