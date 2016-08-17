# This is the base Vagrantfile used to create the Endeavour development box.

#Vagrant.configure("1") do |config|
  #config.vm.boot_mode = :gui
#end


Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"
  #config.vm.box = "ubuntu/trusty32"

  config.vm.provider "virtualbox" do |v|
      v.customize ["modifyvm", :id, "--cpuexecutioncap", "80"]
      v.customize ["modifyvm", :id, "--memory", "2048"]
  end

  ## Guest Config
  config.vm.hostname = "endeavour"
  config.vm.network :private_network, ip: "172.28.128.3"
  #config.vm.network :private_network, type: "dhcp"
  #config.vm.network :private_network, ip: "192.168.0.300"
  config.vm.network :forwarded_port, guest:6633, host:6637 # forwarding of port

  #Configure proxy if testbed environemnt is set 
  #use ENV='testbed' vagrant up
  if ENV['ENV'] == 'testbed' 
  	config.proxy.http     = "http://proxy.zen:8080"
  	config.proxy.https    = "http://proxy.zen:8080"
  	config.proxy.no_proxy = "localhost,127.0.0.1"
  end

  config.vm.network :forwarded_port, guest:6633, host:6637 # open flow controller
  config.vm.network :forwarded_port, guest:3000, host:3000 # grafana

  ## Provisioning
  config.vm.provision :shell, privileged: true, :inline => "apt-get update && apt-get install -y git python-oslo.config"
  config.vm.provision :shell, privileged: false, :inline => "git clone https://github.com/h2020-endeavour/iSDX.git"
  config.vm.provision :shell, privileged: false, :inline => "cd iSDX && bash setup/basic-setup.sh"
  config.vm.provision :shell, privileged: false, :inline => "cd iSDX && bash setup/ovs-setup.sh"
  config.vm.provision :shell, privileged: false, :inline => "cd iSDX && bash setup/mininet-setup.sh"
  config.vm.provision :shell, privileged: false, :inline => "cd iSDX && bash setup/ryu-setup.sh"
  config.vm.provision :shell, privileged: false, :path => "setup/grafana-setup.sh"
  config.vm.provision :shell, privileged: false, :inline => "cd iSDX && bash setup/sdx-setup.sh"

  ## SSH config
  config.ssh.forward_x11 = true

  #config.vm.synced_folder ".", "/home/vagrant/endeavour", type: "rsync",
    #rsync__exclude: ".git/"
  config.vm.synced_folder ".", "/home/vagrant/endeavour"
  #config.vm.synced_folder ".", "/home/vagrant/endeavour", owner: "quagga", group: "quaggavty"

end
