Vagrant.configure("2") do |config|
    config.vm.box = "generic/ubuntu1604"
    config.vm.hostname = "unv.deploy"
    config.vm.network "private_network", ip: "10.51.21.11"
    
    config.vm.provider "virtualbox" do |v|
        v.name = 'unv_deploy_testing'
        v.memory = 512
        v.cpus = 2
        v.customize ["modifyvm", :id, "--uartmode1", "disconnected"]
    end

    config.vm.synced_folder ".", "/vagrant", disabled: true
    
    ssh_pub_key = File.readlines("#{Dir.home}/.ssh/id_rsa.pub").first.strip
    config.ssh.insert_key = false
    config.vm.provision 'shell', inline: 'rm -rf /root/.ssh'
    config.vm.provision 'shell', inline: 'mkdir -p /root/.ssh'
    config.vm.provision 'shell',
        inline: "echo #{ssh_pub_key} >> /root/.ssh/authorized_keys"
    config.vm.provision 'shell',
        inline: "echo #{ssh_pub_key} >> /home/vagrant/.ssh/authorized_keys",
        privileged: false
end
