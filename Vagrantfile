# -*- mode: ruby -*-
# vi: set ft=ruby :
#
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStack Collaborative
#
# This Vagrant file deploys two *independent* OpenStack instances. And
# then configures them so they can interpret the `--scope` for
# collaboration between services.
#

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

  # Configuration of OpenStack instances
  os_confs = [
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

  # Start OpenStacks
  os_confs.each do |os_conf|
    make_os config, os_conf, os_confs
  end
end

# ------------------------------------------------------------------------
# Utils

def run_ansible(vm, name, vars)
  vm.provision name, type: :ansible_local do |ansible|
    ansible.install_mode = "pip"
    ansible.version = "2.6.11"
    ansible.compatibility_mode = "2.0"
    ansible.playbook = "#{name}.yml"
    ansible.extra_vars = vars
    # ansible.verbose = "-vvvv"
  end
end

# Make a new *independant* OpenStack instance.
#
# The creation of the OpenStack instance goes through two provisioning
# phase:
#
# 1. --provision-with setup :: Deploys OS with Devstack
# 2. --provision-with scope :: Deploys HAProxy and set the scope
#    interpretation.
def make_os(config, os_conf, os_confs)
  config.vm.define os_conf[:name] do |os|
    # exit!
    os.vm.hostname = os_conf[:name]
    os.vm.network :private_network, ip: os_conf[:ip], auto_config: true
    os.vm.network :forwarded_port, guest: 22, host: os_conf[:ssh], id: "ssh"
    #os.vm.network :forwarded_port, guest: 80, host: 8881

    # Setup and Install devstack
    run_ansible(os.vm, "setup", {
        :os_name => os_conf[:name],
        :os_ip => os_conf[:ip]
      })

    # Interpret the scope
    run_ansible(os.vm, "scope", {
      :the_conf => os_conf,
      :os_confs => os_confs
    })
  end
end
