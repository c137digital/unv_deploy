Vagrant.configure("2") do |config|
    config.vm.box = "generic/ubuntu1604"
    config.vm.provider "virtualbox" do |v|
        v.memory = 512
        v.cpus = 1
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

    config.vm.define "unvdeploy.test.1" do |app|
        app.vm.network "private_network", ip: "10.10.30.10"
        app.vm.provider "virtualbox" do |v|
            v.name = 'unv_deploy_test_1'
        end
    end

    config.vm.define "unvdeploy.test.2" do |app|
        app.vm.network "private_network", ip: "10.10.30.11"
        app.vm.provider "virtualbox" do |v|
            v.name = 'unv_deploy_test_2'
        end
    end
end
