try:
    from    maya import cmds
    import  json
except:
    pass


class MayaObject(object):
    ''' Object representing an object in Maya.
    Linked to a transform in the scene.
    Can contains shotgrid related data.
    '''

    def __init__(self, root=""):
        ''' Initialize the object.

        Args:
            root    (str,   optional)   : The root transform of the object.
                                        Defaults to "".
        '''
        self._root = root
        # Add the metadatas attributes to the root.
        self.addMetadatas()

    def metadatasExist(self):
        ''' Check if the metadatas already exist on the root.
        '''
        return cmds.attributeQuery("sg_metadatas", node=self._root, exists=True)

    def addMetadatas(self):
        ''' Add the metadatas attributes on the root.
        '''
        if (not self.metadatasExist()):
            cmds.addAttr(self._root, ln="sg_metadatas", nn="SG Metadatas", dt="string")

    def hasNameSpace(self):
        ''' Check if the object has a namespace.
        '''
        return self._root.find(":") != -1

    def isReferenced(self):
        ''' Check if the object is referenced.
        '''
        return cmds.referenceQuery(self._root, isNodeReferenced=True)
    
    def isStandin(self):
        ''' Check if the object is standin type.
        '''
        shapes = cmds.listRelatives(self._root, shapes=True, fullPath=True)
        if(len(shapes)):
            if(cmds.nodeType(shapes[0]) == "standin"):
                return True

        return False

    def isValid(self):
        ''' Perform validation functions for the object. Must be implemented in the child class.

        Returns:
            bool: True if valid, otherwise False.
        '''
        raise NotImplementedError()

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

    @property
    def name(self):
        if(self.hasNameSpace()):
            return self._root.split(":")[0].split("_")[0]
        return self._root.split("_")[0]

    @name.setter
    def name(self, value):
        if(self.hasNameSpace()):
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
    def fullname(self):
        return self._root
    
    @fullname.setter
    def fullname(self, value):
        cmds.rename(self._root, value)

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

