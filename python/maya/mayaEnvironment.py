from .mayaObject    import MayaObject
from .mayaAsset     import MayaAsset

try:
    from    maya import cmds
    import  json
except:
    pass


class MayaEnvironment(MayaObject):
    ''' Object representing an environment in Maya.'''

    def getGroup(self, parent, groupName):
        ''' Get a group from the parent object.
        The group need to be direclty under the asset root in the hierarchy.

        Args:
            parent      (str):  The parent of the group.
            groupName   (str): The group name

        Returns:
            str: The group full path.
        '''
        subGroups = cmds.listRelatives(parent, allDescendents=False, type="transform", fullPath=True)

        for group in subGroups:
            if(group.find(groupName) != -1):
                return group
        
        return None

    def getAssets(self):
        ''' Get the assets in the environment.
        
        Returns:
            list(:class:`MayaAsset`)    : The assets in the environment.
        '''
        # Get the content of the environment.
        content = cmds.listRelatives(self.groupMeshes, allDescendents=True, type="transform", fullPath=True)

        # Loop over the content and get the assets.
        assets = []
        for transform in content:
            # Check the end tag.
            if(transform.endswith("_RIG")):
                asset = MayaAsset(transform)
                assets.append(asset)

        # Return the assets.
        return assets

    def getAssetMainBuffers(self, asset):
        ''' Get the main buffers of an asset.
        
        Args:
            asset (:class:`MayaAsset`)  : The asset to get the main buffers.
        
        Returns:
            list(str)   : The main buffers of the asset.
        '''
        # Get the direct children of the asset.
        # Get the highest level of the asset in priority.
        buffers = []
        if(len(asset.meshesHI) > 0):
            buffers = asset.meshesHI
        elif(len(asset.meshesMI) > 0):
            buffers = asset.meshesMI
        elif(len(asset.meshesLO) > 0):
            buffers = asset.meshesLO
        # Filter the buffers.
        buffers = [child for child in buffers if child.endswith("_BUF")]

        # Return the buffers.
        return buffers

    def getAllAssetsMainBuffers(self):
        ''' Get all the main buffers of the assets in the environment.
        
        Returns:
            list(str)   : The main buffers of the assets in the environment.
        '''
        # Get the assets.
        assets = self.getAssets()

        # Get the main buffers of the assets.
        buffers = []
        for asset in assets:
            buffers.extend(self.getAssetMainBuffers(asset))

        # Return the buffers.
        return buffers

    @property
    def groupMeshes(self):
        return self.getGroup(self._root, "meshes_GRP")