from .mayaObject    import MayaObject
from .mayaAsset     import MayaAsset

try:
    from    maya import cmds
    import  json
except:
    pass


class MayaEnvironment(MayaObject):
    ''' Object representing an environment in Maya.'''

    def isValid(self):
        return self.groupMeshes

    def getGroup(self, parent, groupName):
        ''' Get a group from the parent object.
        The group need to be direclty under the asset root in the hierarchy.

        Args:
            parent      (str):  The parent of the group.
            groupName   (str): The group name

        Returns:
            str: The group full path.
        '''
        subGroups = cmds.listRelatives(parent, allDescendents=False, type="transform", fullPath=True) or []

        for group in subGroups:
            # Get the group short name.
            groupShortName = group.split("|")[-1]
            # Remove the namespace.
            groupShortName = groupShortName.split(":")[-1]
            # Check if the group name is the same.
            if(groupShortName == groupName):
                return group
        
        return None

    def getAssets(self):
        ''' Get the assets in the environment.
        
        Returns:
            list(:class:`MayaAsset`)    : The assets in the environment.
        '''
        # Get the content of the environment.
        content = cmds.listRelatives(self.groupMeshes, allDescendents=True, type="transform", fullPath=True) or []

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

    def getAnimation(self, animated=True, deformed=True):
        ''' Get the animation of the environment.
        
        Args:
            animated    (bool,  optional)   : Get the animated objects.
                                            Defaults to True.
            deformed    (bool,  optional)   : Get the deformed objects.
                                            Defaults to True.
        
        Returns:
            list, list                      : The animated and deformed list of object.
        '''
        # Get the assets.
        assets = self.getAssets()

        # Get the animation of the assets.
        animatedAssets = []
        deformedAssets = []
        for asset in assets:
            
            if(deformed):
                # The asset must be deformed.
                if(asset.isDeformed()):
                    deformedAssets.append(asset)
            
            if(animated):
                # The asset must have animation without being deformed.
                if(asset.isAnimated() and not asset.isDeformed()):
                    animatedAssets.append(asset)

        # Return the animation.
        return animatedAssets, deformedAssets

    @property
    def groupMeshes(self):
        return self.getGroup(self._root, "meshes_GRP")