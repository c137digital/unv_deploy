Vagrant.configure("2") do |config|
    # assign ip in private network
    config.vm.network "private_network", type: "dhcp"

    # disable default mount folder
    config.vm.synced_folder ".", "/vagrant", disabled: true

    # make ssh for root
    ssh_pub_key = File.readlines("#{Dir.home}/.ssh/id_rsa.pub").first.strip
    config.ssh.insert_key = false
    config.vm.provision 'shell', inline: 'rm -rf /root/.ssh'
    config.vm.provision 'shell', inline: 'mkdir -p /root/.ssh'
    config.vm.provision 'shell',
        inline: "echo #{ssh_pub_key} >> /root/.ssh/authorized_keys"
    config.vm.provision 'shell',
        inline: "echo #{ssh_pub_key} >> /home/vagrant/.ssh/authorized_keys",
        privileged: false

    
    config.vm.define "dev-backend-django-1" do |app|
        app.vm.box = "generic/debian11"
        app.vm.hostname = "dev-backend-django-1"

        
        app.vm.provider "parallels" do |v|
            v.name = "dev-backend-django-1"
            v.cpus = "1"
            v.memory = 512
        end
        
    end
    
    config.vm.define "dev-frontend-nginx-1" do |app|
        app.vm.box = "generic/debian11"
        app.vm.hostname = "dev-frontend-nginx-1"

        
        app.vm.provider "parallels" do |v|
            v.name = "dev-frontend-nginx-1"
            v.cpus = "1"
            v.memory = 512
        end
        
    end
    
    config.vm.define "dev-db-postgres-1" do |app|
        app.vm.box = "generic/debian11"
        app.vm.hostname = "dev-db-postgres-1"

        
        app.vm.provider "parallels" do |v|
            v.name = "dev-db-postgres-1"
            v.cpus = "1"
            v.memory = 256
        end
        
    end
    
    config.vm.define "dev-db-redis-1" do |app|
        app.vm.box = "generic/debian11"
        app.vm.hostname = "dev-db-redis-1"

        
        app.vm.provider "parallels" do |v|
            v.name = "dev-db-redis-1"
            v.cpus = "1"
            v.memory = 256
        end
        
    end
    
end
