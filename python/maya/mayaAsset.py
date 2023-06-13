
try:
    from    maya import cmds
    import  json
except:
    pass


class MayaAsset(object):

    def __init__(self, assetRoot=""):

        self._root = assetRoot

        self.addMetadatas()

    def __eq__(self, other):
        return self._root == other._root

    def metadatasExist(self):
        ''' Check if the metadatas already exist on the asset root.
        '''
        return cmds.attributeQuery("sg_metadatas", node=self._root, exists=True)

    def addMetadatas(self):
        ''' Add the metadatas attributes on the asset root.
        '''
        if (self.metadatasExist() == False):
            cmds.addAttr(self._root, ln="sg_metadatas", nn="SG Metadatas", dt="string")

    def getAssetNamespaces(self):
        ''' Get all the namespaces contained in the current asset.

        Returns:
            list    : The list of namespaces.
        '''
        # Get the all the asset child transforms.
        assetDatas = cmds.listRelatives(self._root, allDescendents=True, type="transform")

        # Store all the namespaces in a list.
        assetNamespaces = []
        for element in assetDatas:
            # Check if the name contains a namespace>
            if(element.find(":") != -1):
                # Split the name and the namespace.
                namespace = element.split(":")[0]
                # Check if the namespace is not already in the list.
                if not(namespace in assetNamespaces):
                    # Add the namespace to the list.
                    assetNamespaces.append(namespace)

        # Return the list of namespaces.
        return assetNamespaces

    def freezeNamespace(self):
        ''' Include the namespace in the object naming.
        '''
        # Get the all namespaces in the current asset.
        allNamespaces = self.getAssetNamespaces()
        # Set the current namespace to root.
        cmds.namespace(setNamespace=":")
        # Loop over the asset to merge the namespace with the object name.
        for np in allNamespaces:
            # Get all the objects in the namespace.
            # Use the full path to avoid errors if two objects have the same name.
            npObjects = cmds.namespaceInfo(np, listNamespace=True, dagPath=True)
            # Reorder the objects by path length, to have the farthest objects renamed first.
            # This will avoid errors where Maya can no longer find an object because
            # an element in the path has changed.
            npObjects.sort(key = lambda x : len(x.split('|')) , reverse = True)
            # Loop over the objects and rename them.
            for obj in npObjects:
                # Get the shortname.
                shortName = obj.split("|")[-1]
                # Replace the : by a _.
                newName = shortName.replace(":", "_")
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

    def isStandin(self):
        ''' Check if the asset is standin type.
        '''
        shapes = cmds.listRelatives(self._root, shapes=True, fullPath=True)
        if(len(shapes)):
            if(cmds.nodeType(shapes[0]) == "standin"):
                return True

        return False

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
        self.groupMeshesTechnical is not None and \
        self.groupMeshesTechnicalAll is not None and \
        self.groupMeshesTechnicalHI is not None and \
        self.groupMeshesTechnicalMI is not None and \
        self.groupMeshesTechnicalLO is not None


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

    def getChildReferences(self):
        ''' Get all the references contained in the current asset.
        For instance, the modules for the rig.

        Returns:
            list    : The list of references.
        '''
        # Get the all the asset child transforms.
        assetDatas = cmds.listRelatives(self._root, allDescendents=True, type="transform", fullPath=True)

        # Store all the referenceNodes in a list.
        referencesNodes = []
        for element in assetDatas:
            # Check if the element if referenced.
            if( cmds.referenceQuery(element, isNodeReferenced=True) ):
                # Get the reference node.
                refNode = cmds.referenceQuery(element, referenceNode=True)
                # Check if the reference node is not already in the list.
                if(not refNode in referencesNodes):
                    # Add the reference node to the list.
                    referencesNodes.append(refNode)
                
        # Return the list of references.
        return referencesNodes

    def getBuffers(self, parentGroup, relativePath=False):
        ''' Get all the buffers contained in the current group.

        Args:
            parentGroup     (str)               : The parent group of the buffers.
            relativePath    (bool,  optional)   : If True, the path will be relative to the parent group.
                                                Defaults to False.

        Returns:
            list                                : The list of buffers with.
        '''
        # Get the all the asset child transforms.
        assetDatas = cmds.listRelatives(parentGroup, allDescendents=True, type="transform", fullPath=True)
        # List relatives can return None if there is no transform.
        if(not assetDatas):
            return []

        # Get all the transforms that ends with _BUF.
        buffers = [node for node in assetDatas
            if (node.endswith('_BUF'))
        ]

        # If the relative path is True.
        if(relativePath):
            buffers = [buffer.replace(parentGroup, "") for buffer in buffers]

        # Return the list of buffers.
        return buffers

    def deleteMeshesLO(self):
        ''' Delete the meshes in the low group.
        '''
        # Delete the low meshes.
        cmds.delete(self.meshesLO)
        # Delete the low techincal group.
        cmds.delete(self.meshesTechnicalLO)

    def deleteMeshesMI(self):
        ''' Delete the meshes in the middle group.
        '''
        # Delete the mid meshes.
        cmds.delete(self.meshesMI)
        # Delete the mid techincal group.
        cmds.delete(self.meshesTechnicalMI)

    def deleteMeshesHI(self):
        ''' Delete the meshes in the middle group.
        '''
        # Delete the high meshes.
        cmds.delete(self.meshesHI)
        # Delete the high techincal group.
        cmds.delete(self.meshesTechnicalHI)

    def deleteMeshesTechnical(self):
        ''' Delete the meshes in the technical group.
        '''
        cmds.delete(self.meshesTechnical)

    def importChildReferences(self):
        ''' Import all the references contained in the current asset.
        '''
        # Get the references.
        references = self.getChildReferences()
        # Loop over the references.
        for ref in references:
            # Import the reference.
            refFile = cmds.referenceQuery(ref, filename=True)
            cmds.file(refFile, importReference=True)

    def cleanMetadatas(self, metadatas):
        ''' Clean the shotgrid metadatas to keep only the usefull datas.

        Args:
            metadatas (dict): The shotgrid metadata.

        Returns:
            dict: The cleaned metadatas.
        '''
        cleanedMetadatas = {
            "code"              : metadatas["code"],
            "entity"            : metadatas["entity"],
            "id"                : metadatas["id"],
            "name"              : metadatas["name"],
            "task"              : metadatas["task"],
            "version_number"    : metadatas["version_number"],
        }

        return cleanedMetadatas

    def hasKeyframe(self, node):
        ''' Check if the node has keyframe.

        Args:
            node (str): The node to check.

        Returns:
            bool: True if the node has keyframe, False otherwise.
        '''
        return cmds.keyframe(node, query=True, name=True) != None

    def isAnimated(self):
        ''' Check if the asset is animated.

        Returns:
            bool: True if the node is animated, False otherwise.
        '''
        # Get the controllers.
        controllers = cmds.listRelatives(
            self.groupRig,
            allDescendents = True,
            type='transform'
        )
        if(not controllers):
            return False
        
        hasKey = False
        for con in controllers:
            # Skip if the controller is not tag as controller.
            if(not con.endswith('_CON')):
                continue
            
            # Check if the controller has keyframe.
            if(self.hasKeyframe(con)):
                hasKey = True
                break
        
        return hasKey

    def isDeformed(self):
        ''' Check if the asset is deformed.

        Returns:
            bool: True if the node is deformed, False otherwise.
        '''

        meshesGrp = []
        if(self.groupMeshesHI):
            meshesGrp.append(self.groupMeshesHI)
        if(self.groupMeshesMI):
            meshesGrp.append(self.groupMeshesMI)
        if(self.groupMeshesLO):
            meshesGrp.append(self.groupMeshesLO)

        # Get the shapes.
        shapes = cmds.listRelatives(
            meshesGrp,
            allDescendents = True,
            type='mesh'
        ) or []

        # Get the origShapes.
        origShapes = [shape for shape in shapes if shape.endswith('ShapeOrig')]

        return True if len(origShapes) > 0 else False

    @property
    def name(self):
        if(self.asNameSpace()):
            return self._root.split('|')[-1].split(":")[0].split("_")[0]
        return self._root.split('|')[-1].split("_")[0]

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
            return int(self._root.split('|')[-1].split(":")[0].split("_")[1])
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
    def groupMeshesTechnicalAll(self):
        return self.getGroup(self.groupMeshesTechnical, "ALL_GRP")

    @property
    def groupMeshesTechnicalHI(self):
        return self.getGroup(self.groupMeshesTechnical, "HI_GRP")
    
    @property
    def groupMeshesTechnicalMI(self):
        return self.getGroup(self.groupMeshesTechnical, "MI_GRP")
    
    @property
    def groupMeshesTechnicalLO(self):
        return self.getGroup(self.groupMeshesTechnical, "LO_GRP")

    @property
    def meshesHI(self):
        content = cmds.listRelatives(self.groupMeshesHI, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def meshesMI(self):
        content = cmds.listRelatives(self.groupMeshesMI, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def meshesLO(self):
        content = cmds.listRelatives(self.groupMeshesLO, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def meshesTechnical(self):
        content = cmds.listRelatives(self.groupMeshesTechnical, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def meshesTechnicalGlobal(self):
        content = cmds.listRelatives(self.groupMeshesTechnicalGlobal, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def meshesTechnicalHI(self):
        content = cmds.listRelatives(self.groupMeshesTechnicalHI, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def meshesTechnicalMI(self):
        content = cmds.listRelatives(self.groupMeshesTechnicalMI, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def meshesTechnicalLO(self):
        content = cmds.listRelatives(self.groupMeshesTechnicalLO, children=True, fullPath=True, type="transform")
        content = content if content else []
        return content

    @property
    def referenceNode(self):
        if(self.isReferenced()):
            return cmds.referenceQuery(self._root, referenceNode=True)
        return None
    
    @property
    def referencePath(self):
        reference = self.referenceNode
        if(reference):
            return cmds.referenceQuery(reference, filename=True).split("{")[0]
        return None
    
    @referencePath.setter
    def referencePath(self, value):
        reference = self.referenceNode
        if(reference):
            cmds.file(value, loadReference=reference, type="mayaAscii")

    @property
    def rootNamespace(self):
        return self._root.split(":")[0] if self._root.find(":") != -1 else None

    @property
    def sgMetadatas(self):
        return json.loads(cmds.getAttr("%s.sg_metadatas" % self._root))
    
    @sgMetadatas.setter
    def sgMetadatas(self, value):
        # Clean the metadatas.
        metadatas = self.cleanMetadatas(value)
        # Set the metadatas value.
        cmds.setAttr("%s.sg_metadatas" % self._root, json.dumps(metadatas), type="string")

    @property
    def sgCode(self):
        return self.sgMetadatas["code"]

    @property
    def sgEntity(self):
        return self.sgMetadatas["entity"]
    
    @property
    def sgEntityName(self):
        return self.sgEntity["name"]
    
    @property
    def sgID(self):
        return self.sgMetadatas["id"]

    @property
    def sgTask(self):
        return self.sgMetadatas["task"]

    @property
    def sgTaskName(self):
        return self.sgTask["name"]

    @property
    def sgVersionNumber(self):
        return self.sgMetadatas["version_number"]
