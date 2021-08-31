class ProviderServerManager:
    async def list_instances(self):
        pass

    async def create_instance(self, name, tags, force=False):
        """Create server with tags, or delete existing if force=True"""
        pass

    async def delete_instance(self, name):
        pass

    async def cleanup_instances(self):
        """Find all servers that not used and destroy them."""
        # get current servers
        # get all servers we want to use
        # list 
