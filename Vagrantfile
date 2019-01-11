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

  # Start OpenStacks
  make_os config, "RegionOne", "192.168.141.245", primary=true
  make_os config, "RegionTwo", "192.168.142.245"
end

# ------------------------------------------------------------------------
# Utils

# Make a new *independant* OpenStack instance.
def make_os(config, os_name, ip, primary = false)
  config.vm.define os_name, primary: primary do |os|
    # exit!
    #os.vm.network :forwarded_port, guest: 80, host: 8881
    os.vm.hostname = os_name
    os.vm.network :private_network, ip: ip, auto_config: true
    os.vm.provision :ansible_local do |ansible|
      ansible.install_mode = "pip"
      ansible.version = "2.6.11"
      ansible.compatibility_mode = "2.0"
      ansible.playbook = "provision.yml"
      # ansible.verbose = "-vvvv"
      ansible.extra_vars = {
        :os_name => os_name,
        :os_ip => ip
      }
    end
  end
end
