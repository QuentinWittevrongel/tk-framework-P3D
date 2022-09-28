
# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    from maya           import cmds
    from maya           import mel
    from tank_vendor    import six

    import sgtk
    import os

except:
    pass

from .mayaAsset import MayaAsset

class LoadTools(object):

    def __init__(self):
        pass

    def importAssetAsReference(self, assetName, path, sg_publish_data):
        ''' Import the asset as reference.

        Args:
            assetName   (str): The asset name.
            path        (str): The path to reference.

        Return:
            :class:`MayaAsset`: The new aasset instance.
        '''
        # Check if instance already exist in the current scene.
        lastInstance = self.getAssetLastInstances(assetName)
        # Define the current instance number.
        instanceNumber = 1
        if(lastInstance):
            instanceNumber = lastInstance.instance + 1
        # Create the instance namespace.
        assetNamespace = '%s_%03d' % (assetName, instanceNumber)
        # Import asset as reference.
        nodes = cmds.file(
            path,
            reference=True,
            loadReferenceDepth="all",
            mergeNamespacesOnClash=False,
            namespace=assetNamespace,
            returnNewNodes=True
        )
        asset = MayaAsset(assetRoot=nodes[1])
        asset.sgMetadatas = sg_publish_data

        return asset

    def importAsset(self, assetName, path, sg_publish_data):
        
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        nodes = cmds.file(
            path,
            i=True,
            type="mayaAscii",
            returnNewNodes=True
        )

        asset = MayaAsset(assetRoot=nodes[0])
        asset.sgMetadatas = sg_publish_data

        return asset

    def importAssetAsStandin(self, assetName, path):
        pass

    def importAssetRig(self, assetName, rigResolution, path):
        pass

    def replaceAssetRig(self, assetName, rigResolution, path):
        pass

    def replaceSelectedAssetsReference(self, assetName, path):
        ''' Select the asset reference then replace the reference file with the new one.

        Args:
            assetName   (str)   : The name of the asset instance to replace.
            path        (str)   : The new path for the asset instance reference.
        '''
        # Get the current selected asset.
        selection = cmds.ls(sl=True, type="transform")
        if(len(selection) > 0):
            for sel in selection:
                print(sel)
                asset = MayaAsset(assetRoot=sel)
                if(asset.isValid() and asset.name == assetName and asset.isReferenced()):
                    asset.referencePath = path
                else:
                    print("WARNING : The current selected object '%s' is not a valid referenced asset." % sel)
        else:
            raise TypeError()

    def getAssetInstances(self, assetName):
        ''' Get the instances of the asset.

        Args:
            assetName (str): The asset name.

        Returns:
            list(str): The asset's instances.
        '''
        return [MayaAsset(assetRoot=asset) for asset in cmds.ls(type="transform") if asset.find(":") != -1 and asset.split(":")[0].split("_")[0] == assetName]

    def getAssetLastInstances(self, assetName):
        ''' Get the last asset instance.

        Args:
            assetName (str): The asset name.

        Returns:
            :class:`MayaAsset`: The last asset instance.
        '''
        instanceNumber  = 0
        lastInstance    = None

        for asset in self.getAssetInstances(assetName):
            if(asset.instance >= instanceNumber):
                instanceNumber  = asset.instance
                lastInstance    = asset

        return lastInstance