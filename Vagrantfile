Vagrant.configure("2") do |config|
    name = 'unvdeploytest'

    config.vm.box = "generic/debian10"
    ip = "10.10.30.10"
    memory = 512
    cpus = 2
    
    config.vm.provider "virtualbox" do |v|
        v.memory = memory
        v.cpus = cpus
        v.customize ["modifyvm", :id, "--uartmode1", "disconnected"]
        v.customize ["modifyvm", :id, "--vram", "12"]
    end

    config.vm.provider "parallels" do |prl|
        prl.memory = memory
        prl.cpus = cpus
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

    config.vm.define "app" do |app|
        app.vm.network "private_network", ip: ip
        app.vm.hostname = name

        app.vm.provider "virtualbox" do |v|
            v.name = name
        end

        app.vm.provider "parallels" do |v|
            v.name = name
        end
    end
end

