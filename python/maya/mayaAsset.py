# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    from maya import cmds
except:
    pass


class MayaAsset(object):

    def __init__(self, assetRoot=""):

        self._root = assetRoot

    def getAssetNamespaces(self):
        ''' Get all the namespace contain in the current asset.
        '''
        # Get the all the asset elements.
        assetDatas = cmds.listRelatives(self._root, allDescendents=True, type="transform")
        
        assetNamespaces = []

        for element in assetDatas:
            if(element.find(":") != -1):
                namespace = element.split(":")[0]
                if not(namespace in assetNamespaces):
                    assetNamespaces.append(namespace)

        return assetNamespaces

    def freezeNamespace(self):
        ''' Include the namespace to the object naming.
        '''
        # Get the all namespace in the current asset.
        allNamespaces = self.getAssetNamespaces()
        # Loop over the asset to merge the namespace with the object name.
        for np in allNamespaces:
            npObjects = cmds.namespaceInfo(np, listNamespace=True)
            for obj in npObjects:
                newName = obj.replace(":", "_")
                cmds.rename(obj, newName)

    def asNameSpace(self):
        ''' Check if the asset is name a namespace.
            If the asset is in a namespace. The name space beacoup the instance name.
        '''
        return self._root.find(":") != -1

    def isReferenced(self):
        ''' Check if the asset is referenced.
        '''
        return cmds.referenceQuery(self._root, isNodeReferenced=True)

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

    def isValid(self):
        ''' Check if the current asset root is a valide production asset.

        Returns:
            bool: True if valid, otherwise False.
        '''
        return self.groupMeshes is not None and \
        self.groupBones is not None and \
        self.groupRig is not None and \
        self.groupMeshesHI is not None and \
        self.groupMeshesMI is not None and \
        self.groupMeshesLO is not None and \
        self.groupMeshesTechnical is not None

    def deleteMeshesLO(self):
        ''' Delete the meshes in the low group.
        '''
        cmds.delete(self.meshesLO)

    def deleteMeshesMI(self):
        ''' Delete the meshes in the middle group.
        '''
        cmds.delete(self.meshesMI)

    def deleteMeshesHI(self):
        ''' Delete the meshes in the middle group.
        '''
        cmds.delete(self.meshesHI)

    def deleteMeshesTechnical(self):
        ''' Delete the meshes in the middle group.
        '''
        cmds.delete(self.meshesTechnical)

    @property
    def name(self):
        if(self.asNameSpace()):
            return self._root.split(":")[0].split("_")[0]
        return self._root.split("_")[0]

    @name.setter
    def name(self, value):
        if(self.asNameSpace()):
            splitNameSpace      = self._root.split(":")
            splitName           = splitNameSpace[0].split("_")
            splitName[0]        = value
            splitNameSpace[0]   = "_".join(splitName)
            cmds.rename(self._root, ":".join(splitNameSpace))

        else:
            splitName = self._root.split("_")
            splitName[0] = value
            cmds.rename(self._root, "_".join(splitName))

    @property
    def instance(self):
        if(self.isReferenced()):
            return  int(self._root.split(":")[0].split("_")[1])
        return None

    @instance.setter
    def instance(self, value):
        if(self.isReferenced()):
            splitNameSpace      = self._root.split(":")
            splitName           = splitNameSpace[0].split("_")
            splitName[1]        = '%3d' % value
            splitNameSpace[0]   = "_".join(splitName)
            cmds.rename(self._root, ":".join(splitNameSpace))

    @property
    def step(self):
        if not(self.isReferenced()):
            return  self._root.split("_")[1]
        return None

    @step.setter
    def step(self, value):
        if not(self.isReferenced()):
            splitName = self._root.split("_")
            splitName[1] = value
            cmds.rename(self._root, "_".join(splitName))

    @property
    def fullname(self):
        return self._root
    
    @fullname.setter
    def fullname(self, value):
        cmds.rename(self._root, value)

    @property
    def groupMeshes(self):
        return self.getGroup(self._root, "meshes_GRP")

    @property
    def groupRig(self):
        return self.getGroup(self._root, "rig_GRP")

    @property
    def groupBones(self):
        return self.getGroup(self._root, "bones_GRP")

    @property
    def groupMeshesHI(self):
        return self.getGroup(self.groupMeshes, "HI_GRP")

    @property
    def groupMeshesMI(self):
        return self.getGroup(self.groupMeshes, "MI_GRP")

    @property
    def groupMeshesLO(self):
        return self.getGroup(self.groupMeshes, "LO_GRP")

    @property
    def groupMeshesTechnical(self):
        return self.getGroup(self.groupMeshes, "Technical_GRP")

    @property
    def meshesHI(self):
        return cmds.listRelatives(self.groupMeshesHI, children=True, fullPath=True, type="transform")

    @property
    def meshesMI(self):
        return cmds.listRelatives(self.groupMeshesMI, children=True, fullPath=True, type="transform")

    @property
    def meshesLO(self):
        return cmds.listRelatives(self.groupMeshesLO, children=True, fullPath=True, type="transform")

    @property
    def meshesTechnical(self):
        return cmds.listRelatives(self.groupMeshesTechnical, children=True, fullPath=True, type="transform")

    @property
    def referenceNode(self):
        if(self.isReferenced()):
            return cmds.referenceQuery(self._root, referenceNode=True)
        return None
    
    @property
    def referencePath(self):
        reference = self.referenceNode
        if(reference):
            return cmds.referenceQuery(reference, filename=True)
        return None
    
    @referencePath.setter
    def referencePath(self, value):
        reference = self.referenceNode
        if(reference):
            cmds.file(value, loadReference=reference, type="mayaAscii")
