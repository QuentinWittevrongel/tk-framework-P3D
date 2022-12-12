
# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    from maya           import cmds
    from maya           import mel
    from tank_vendor    import six

    import sgtk
    import os

except:
    pass

from .mayaObject    import MayaObject
from .mayaAsset     import MayaAsset

class LoadTools(object):

    def __init__(self):
        pass

    def importAsReference(self, name, path, sg_publish_data):
        ''' Import the file as reference.

        Args:
            name                (str)   : The entity name.
            path                (str)   : The path to reference.
            sg_publish_data     (dict)  : The shotgrid publish data.

        Return:
            :class:`MayaObject`         : The new object instance.
        '''
        # Check if the file exists on disk.
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        # Get the last instance number.
        lastInstanceNumber = self.getLastInstanceNumber(name)
        # Create the instance name.
        instanceName = '{NAME}_{INSTANCE:03d}'.format(NAME=name, INSTANCE=lastInstanceNumber + 1)

        # Import file as reference.
        nodes = cmds.file(
            path,
            reference               = True,
            loadReferenceDepth      = "all",
            mergeNamespacesOnClash  = False,
            namespace               = instanceName,
            returnNewNodes          = True
        )

        # Get the root nodes.
        rootNodes = [node for node in nodes if 
            cmds.nodeType(node) == 'transform' and
            cmds.listRelatives(node, parent=True) is None
        ]

        # Get the Maya object and set the shotgrid metadata.
        mayaObject = MayaObject(assetRoot=rootNodes[0])
        mayaObject.sgMetadatas = sg_publish_data

        # Return the Maya object.
        return mayaObject

    def importAsReferenceWithoutNamespace(self, name, path, sg_publish_data):
        ''' Import the file as reference without namespace.

        Args:
            name                (str)   : The entity name.
            path                (str)   : The path to reference.
            sg_publish_data     (dict)  : The shotgrid publish data.

        Return:
            :class:`MayaObject`         : The new object instance.
        '''
        # Check if the file exists on disk.
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        # Get the last instance number.
        lastInstanceNumber = self.getLastInstanceNumber(name)
        # Create the instance name.
        instanceName = '{NAME}_{INSTANCE:03d}'.format(NAME=name, INSTANCE=lastInstanceNumber + 1)

        # Import the file as reference.
        nodes = cmds.file(
            path,
            reference               = True,
            loadReferenceDepth      = 'all',
            mergeNamespacesOnClash  = False,
            namespace               = ':',
            referenceNode           = '{}RN'.format(instanceName),
            returnNewNodes          = True
        )

        # Get the root nodes.
        rootNodes = [node for node in nodes if 
            cmds.nodeType(node) == 'transform' and
            cmds.listRelatives(node, parent=True) is None
        ]

        # Get the Maya object and set the shotgrid metadata.
        mayaObject = MayaObject(root=rootNodes[0])
        mayaObject.sgMetadatas = sg_publish_data

        # Return the Maya object.
        return mayaObject

    def importHard(self, name, path, sg_publish_data):
        ''' Import the file in the scene.

        Args:
            name                (str)   : The entity name.
            path                (str)   : The path to reference.
            sg_publish_data     (dict)  : The shotgrid publish data.

        Return:
            :class:`MayaObject`         : The new object.
        '''
        # Check if the file exists on disk.
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        # Import the file.
        nodes = cmds.file(
            path,
            i=True,
            type="mayaAscii",
            returnNewNodes=True
        )

        # Get the root nodes.
        rootNodes = [node for node in nodes if 
            cmds.nodeType(node) == 'transform' and
            cmds.listRelatives(node, parent=True) is None
        ]

        # Get the Maya object and set the shotgrid metadata.
        mayaObject = MayaObject(root=rootNodes[0])
        mayaObject.sgMetadatas = sg_publish_data

        return mayaObject

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

    def getInstancesByName(self, name):
        ''' Get the instances using the name.

        Args:
            name    (str)   : The name to look for.

        Returns:
            list(str)       : A list of the instance names.
        '''
        # This will take into account the namespaces and the references nodes
        # as we can load references without namespaces.

        # Filter the namespaces to keep only the ones with the same name.
        instances = [ns for ns in cmds.namespaceInfo(listOnlyNamespaces=True) if ns.startswith(name + '_')]
        # Filter the references nodes to keep only the ones with the same name.
        references = [ref for ref in cmds.ls(type='reference') if ref.startswith(name + '_')]
        # Merge the two lists.
        for refNode in references:
            # Get the name without the RN tag.
            refName = refNode.replace('RN', '')
            # Check if the reference node is not already in the instances list.
            if(refName not in instances):
                instances.append(refName)

        return instances

    def getLastInstanceNumber(self, name):
        ''' Get the last instance number of the asset.

        Args:
            name    (str)   : The asset name.

        Returns:
            int             : The last instance number.
        '''
        # Get the instances.
        instances = self.getInstancesByName(name)
        # Get the last instance number.
        lastInstanceNumber = 0
        if(instances):
            lastInstanceNumber = max([int(ns.split('_')[-1]) for ns in instances])

        return lastInstanceNumber