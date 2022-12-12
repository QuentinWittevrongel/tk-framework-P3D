# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    from maya           import cmds

except:
    pass

class TechnicalCheck(object):

    # Define the templates that the nodes can have.
    AvailableNameTemplates   = [
        [           '{NODE_NAME}',                          '{TYPE}'                    ],  # pieds_GRP
        [           '{NODE_NAME}',                          '{TYPE}',   '{RESOLUTION}'  ],  # piedTable_MSH_low
        [           '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}'                    ],  # pieds_000_GRP
        [           '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}',   '{RESOLUTION}'  ],  # piedTable_000_MSH_low
        ['{SIDE}',  '{NODE_NAME}',                          '{TYPE}'                    ],  # L_pieds_GRP
        ['{SIDE}',  '{NODE_NAME}',                          '{TYPE}',   '{RESOLUTION}'  ],  # L_piedTable_MSH_low
        ['{SIDE}',  '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}'                    ],  # L_pieds_000_GRP
        ['{SIDE}',  '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}',   '{RESOLUTION}'  ],  # L_piedTable_000_MSH_low
    ]

    # Define the types of nodes that can be used.
    AvailableNodeTypes = [
        'RIG', 'ENV',
        'MSH', 'BUF', 'GRP', 'CON', 'JNT', 'CAM'
    ]

    def __init__(self):
        ''' Initialize the class.
        '''
        pass

    @classmethod
    def validateAsset(cls, hookClass, mayaAsset):
        ''' Perform the technical check for the asset.

        Args:
            hookClass   (:class:`PublishTask`)  : The hook class.
            mayaAsset   (:class:`MayaAsset`)    : The maya asset to check.

        Returns:
            bool                                : True if the check is valid.
        '''
        validationState = True

        # Check the hierarchy.
        validationState = cls.validateAssetHierarchy(hookClass, mayaAsset)  and validationState

        # Check if the asset has the same buffers in all resolutions.
        validationState = cls.validateAssetBuffers(hookClass, mayaAsset)    and validationState

        # Check the nodes name.
        validationState = cls.validateAssetNodes(hookClass, mayaAsset)      and validationState

        # Return the validation state.
        return validationState

    @classmethod
    def validateAssetHierarchy(cls, hookClass, mayaAsset):
        ''' Validate the asset hierarchy.

        Args:
            hookClass   (:class:`PublishTask`)  : The hook class.
            mayaAsset   (:class:`MayaAsset`)    : The maya asset to check.

        Returns:
            bool                                : True if the check is valid.
        '''
        validationState = True
        # Check the hierarchy.
        if( not mayaAsset.isValid() ):
            validationState = False
            errorMsg = 'The asset hierarchy is not valid.'
            hookClass.logger.error(errorMsg)

        return validationState

    @classmethod
    def validateAssetBuffers(cls, hookClass, mayaAsset):
        ''' Validate that the buffers are the same across resolutions.

        Args:
            hookClass   (:class:`PublishTask`)  : The hook class.
            mayaAsset   (:class:`MayaAsset`)    : The maya asset to check.

        Returns:
            bool                                : True if the check is valid.
        '''
        validationState = True
        # Check if the asset has the same buffers in all resolutions.
        buffers = []
        # Check if there is something in the LO_GRP.
        if(len(mayaAsset.meshesLO) > 0):
            # Get all the buffers and get their path relative to the resolution group.
            resBuffers = mayaAsset.getBuffers( mayaAsset.groupMeshesLO, relativePath = True )
            # Set the list of buffers.
            buffers = resBuffers
            # Sort the list of buffers to be able to compare them.
            buffers.sort()
        
        # Check if there is something in the MI_GRP.
        if(len(mayaAsset.meshesMI) > 0):
            # Get all the buffers and get their path relative to the resolution group.
            resBuffers = mayaAsset.getBuffers( mayaAsset.groupMeshesMI, relativePath = True )
            # If the list of buffers is not set, set it.
            if(not buffers):
                buffers = resBuffers
                buffers.sort()
            
            else:
                resBuffers.sort()
                # Check if the list of buffers is the same.
                if(buffers != resBuffers):
                    validationState = False
                    errorMsg = 'The buffers are not the same in all resolutions.'
                    hookClass.logger.error(errorMsg)

        # Check if there is something in the HI_GRP.
        if(len(mayaAsset.meshesHI) > 0):
            # Get all the buffers and get their path relative to the resolution group.
            resBuffers = mayaAsset.getBuffers( mayaAsset.groupMeshesHI, relativePath = True )
            # If the list of buffers is not set, set it.
            if(not buffers):
                buffers = resBuffers
                buffers.sort()
            
            else:
                resBuffers.sort()
                # Check if the list of buffers is the same.
                if(buffers != resBuffers):
                    validationState = False
                    errorMsg = 'The buffers are not the same in all resolutions.'
                    hookClass.logger.error(errorMsg)

        return validationState

    @classmethod
    def validateAssetNodes(cls, hookClass, mayaAsset):
        ''' Validate the nodes in the asset.

        Args:
            hookClass   (:class:`PublishTask`)  : The hook class.
            mayaAsset   (:class:`MayaAsset`)    : The maya asset to check.

        Returns:
            bool                                : True if the check is valid.
        '''
        validationState = True
        # Get the content of the asset.
        assetContent = cmds.listRelatives(mayaAsset.groupMeshes, allDescendents=True, fullPath=True)

        # Loop through the content of the asset and validate each node.
        for node in assetContent:

            # Get the node data from its name.
            shortName = node.split('|')[-1].split(':')[-1]
            nodeData = cls.getNodeDataFromName(shortName)

            # Validate the naming.
            if(not cls.validateNodeName(hookClass, node)):
                validationState = False
                errorMsg        = 'Validation failed because the node {0} is not valid.'.format(node)
                hookClass.logger.error(errorMsg)

            # Check if a type is defined.
            if(nodeData['type']):
                # If the node is a mesh transform, check for non deformer history.
                if(nodeData['type'][0] == 'MSH'):
                    # Check if the node has non deformer history.
                    if(TechnicalCheck.hasNonDeformerHistory(node)):
                        validationState = False
                        errorMsg        = 'Validation failed because the node {0} has non deformer history.'.format(node)
                        #self.logger.error(errorMsg, extra=self._cleanHistoryAsAction(child))
                        hookClass.logger.error(errorMsg)

                # If the node is a group or a mesh, the pivot point must be at 0, 0, 0.
                if((nodeData['type'][0] == 'GRP' or nodeData['type'][0] == 'BUF') and cmds.nodeType(node) == 'transform'):
                    # Check if there is no transforms.
                    if(TechnicalCheck.hasTransform(node)):
                        validationState = False
                        errorMsg        = 'Validation failed because the transform {0} has a transform.'.format(node)
                        hookClass.logger.error(errorMsg)
                    
                    # Check if the pivot is at identity.
                    if(not TechnicalCheck.isPivotIdentity(node)):
                        validationState = False
                        errorMsg        = 'Validation failed because the transform {0} does not have a pivot at identity.'.format(node)
                        #self.logger.error(errorMsg, extra=self._cleanPivotAsAction(child))
                        hookClass.logger.error(errorMsg)
        
        return validationState

    @classmethod
    def validateNodeName(cls, hookClass, node):
        ''' Validate the node.
        
        Args:
            hookClass   (:class:`PublishTask`)  : The hook class.
            mayaAsset   (:class:`MayaAsset`)    : The maya asset to check.

        Returns:
            bool                                : True if the check is valid.
        '''
        # Set a default validation state to True.
        validationState = True

        # Get the short name of the node without namespace.
        shortName = node.split('|')[-1].split(':')[-1]

        # Get the node data from its name.
        nodeData = cls.getNodeDataFromName(shortName)

        # Get the node type from Maya.
        mayaNodeType = cmds.nodeType(node)

        # Skip the validation for the shapes.
        if(mayaNodeType in ['mesh', 'camera', 'fnk_rig_shape']):
            hookClass.logger.debug('The node {} is a mesh, camera or fnk_rig_shape, we check their parent transform instead.'.format(node))
            return True

        # Get the template of the node.
        nodeTemplate = cls.getTemplateFromName(shortName)
        # Check if the template is valid.
        if(not cls.isTemplateValid(nodeTemplate)):
            hookClass.logger.error('Invalid name template for the node {0}'.format(nodeTemplate))
            return False


        # Compare the maya node type and the name node type.
        if(mayaNodeType == 'transform'):
            # A transform can be a group or a buffer.
            # Or a mesh if the children is a mesh.

            # Get the children of the node.
            nodeChildren = cmds.listRelatives(node, children=True, fullPath=True)
            # cmds.listRelatives() returns None if there is no child.
            nodeChildren = nodeChildren if nodeChildren else []
            # Get a list of the children node type.
            nodeChildrenType = [cmds.nodeType(child) for child in nodeChildren]

            # Check if the node has a type.
            if(nodeData['type']):

                if(nodeData['type'][0] == 'MSH'):
                    # The transform is tagged as a mesh transform.

                    # Check if all the children are meshes.
                    if(not all(childType == 'mesh' for childType in nodeChildrenType)):
                        hookClass.logger.error(
                            'The transform {} is flagged as a mesh transform and does not contains only meshes.'.format(node)
                        )
                        return False

                    # Check if the name is correct.
                    validationState = cls.validateName(
                        hookClass,
                        node,
                        nodeData,
                        forceType       = ['MSH'],
                        resolution      = 'required'
                    ) and validationState

                elif(nodeData['type'][0] == 'CON'):
                    # Check if all the children are fnk_rig_shape.
                    if(not 'fnk_rig_shape' in nodeChildrenType):
                        hookClass.logger.error(
                            'The transform {} is flagged as a controller transform and does not contains only fnk_rig_shape.'.format(node)
                        )
                        return False

                    # Check if the name is correct.
                    validationState = cls.validateName(
                        hookClass,
                        node,
                        nodeData,
                        forceType       = ['CON'],
                        resolution      = 'notrequired'
                    ) and validationState

                elif(nodeData['type'][0] == 'CAM'):
                    # Check if all the children are cameras.
                    if(not all(childType == 'camera' for childType in nodeChildrenType)):
                        hookClass.logger.error(
                            'The transform {} is flagged as a camera transform and does not contains only camera.'.format(node)
                        )
                        return False

                    # Check if the name is correct.
                    validationState = cls.validateName(
                        hookClass,
                        node,
                        nodeData,
                        forceType       = ['CAM'],
                        resolution      = 'notrequired'
                    ) and validationState

                elif(nodeData['type'][0] == 'GRP' or nodeData['type'][0] == 'BUF'):
                    # Check if all the children are transforms ot joints.
                    if(not all(childType == 'transform' or childType == 'joint' for childType in nodeChildrenType)):
                        hookClass.logger.error(
                            'The transform {} is flagged as a transform and does not contains only transform or joint.'.format(node)
                        )
                        return False

                    # Check if the name is correct.
                    validationState = cls.validateName(
                        hookClass,
                        node,
                        nodeData,
                        forceType       = ['GRP', 'BUF'],
                        resolution      = 'notrequired'
                    ) and validationState

                else:
                    hookClass.logger.error('The node {} is a transform and can not be {}.'.format(node, shortName.split('_')[-1]))
                    return False
  
        elif(mayaNodeType == 'joint'):
            # Check if the name is correct.
            validationState = cls.validateName(
                hookClass,
                node,
                nodeData,
                forceType       = ['JNT'],
                resolution      = 'notrequired'
            ) and validationState

        else:
            hookClass.logger.debug('The validation for the node {} is not yet supported.'.format(node))

        # The node is valid.
        return validationState

    @classmethod
    def validateName(self, hookClass, nodePath, nodeData, forceType=[], side='optional', name='required', instanceNumber='optional', type='required', resolution='optional'):
        ''' Validate the name of the given node.

        Args:
            hookClass               (:class:`PublishTask`)  : The hook class.
            nodePath                (str)                   : The path of the node.
            nodeTemplate            (dict)                  : The data of the node.
            forceType               (list,  optional)       : The list of the type the node can have.                                               Default to [].
            side                    (str,   optional)       : The side of the node.                     Can be required, unrequired or optional.    Default to 'optional'.
            name                    (str,   optional)       : The name of the node.                     Can be required, unrequired or optional.    Default to 'required'.
            instanceNumber          (str,   optional)       : The instance number of the node.          Can be required, unrequired or optional.    Default to 'optional'.
            type                    (str,   optional)       : The type of the node.                     Can be required, unrequired or optional.    Default to 'required'.
            resolution              (str,   optional)       : The resolution of the node.               Can be required, unrequired or optional.    Default to 'optional'.

        Return:
            bool                                            : defaultState if the name is valid, False otherwise.
        '''
        # Set a default validation state to True.
        validationState = True

        # Check if the type is forced.
        if(forceType):
            checkType = False
            # Loop though the forced types.
            for type in forceType:
                # Check if the type is in the node data.
                if(type in nodeData['type']):
                    # The type is valid.
                    checkType = True
                    break

            # Check if the type is valid.
            if(not checkType):
                validationState = False
                errorMsg        = "The type of the node {0} is not valid. It should be one of the following: {1}".format(nodePath, forceType)
                hookClass.logger.error(errorMsg)


        # Check if the node has a side.
        if(side == 'unrequired' and nodeData['side'] ):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must not contain a side.".format(nodePath)
            self._logger.error(errorMsg)
        elif(side == 'required' and not nodeData['side']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must contain a side.".format(nodePath)
            hookClass.logger.error(errorMsg)

        # Check if the node has a name.
        if(name == 'unrequired' and nodeData['name']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must not contain a name.".format(nodePath)
            hookClass.logger.error(errorMsg)
        elif(name == 'required' and not nodeData['name']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must contain a name.".format(nodePath)
            hookClass.logger.error(errorMsg)
        
        # Check if the node has an instance number.
        if(instanceNumber == 'unrequired' and nodeData['instanceNumber']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must not contain an instance number.".format(nodePath)
            hookClass.logger.error(errorMsg)
        elif(instanceNumber == 'required' and not nodeData['instanceNumber']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must contain an instance number.".format(nodePath)
            hookClass.logger.error(errorMsg)

        # Check if the node has a type.
        if(type == 'unrequired' and nodeData['type']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must not contain a type.".format(nodePath)
            hookClass.logger.error(errorMsg)
        elif(type == 'required' and not nodeData['type']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must contain a type.".format(nodePath)
            hookClass.logger.error(errorMsg)

        # Check if the node has a resolution.
        if(resolution == 'unrequired' and nodeData['resolution']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must not contain a resolution.".format(nodePath)
            hookClass.logger.error(errorMsg)
        elif(resolution == 'required' and not nodeData['resolution']):
            validationState = False
            errorMsg        = "Validation failed because the name of {0} must contain a resolution.".format(nodePath)
            hookClass.logger.error(errorMsg)

        # Return the validation state.
        return validationState

    @classmethod
    def getTemplateFromName(cls, nodeName):
        ''' Get the template from the node name.
        
        Args:
            nodeName (str)  : The name of the node.
        
        Returns:
            list            : The template.
        '''
        # Split the name of the node.
        nodeNameSplit       = nodeName.split('_')
        # Create an array to store the current node template.
        template            = [None] * len(nodeNameSplit)

        # Determin the template type of each element.
        for i, element in enumerate(nodeNameSplit):
            if(element in ['L', 'R', 'M']):                                 # Check if the element is a side
                template[i]                 = '{SIDE}'
            elif(element.isdigit()):                                        # Check if the element is a number.
                template[i]                 = '{INSTANCE_NUMBER}'
            elif(element in cls.AvailableNodeTypes):                        # Check if the element is a type.    
                template[i]                 = '{TYPE}'
            elif(element in ['low', 'mid', 'high', 'sculpt']):              # Check if the element is a resolution.
                template[i]                 = '{RESOLUTION}'
            else:                                                           # Otherwise, the element is the name of the node.
                template[i]                 = '{NODE_NAME}'
        
        # Return the node template.
        return template

    @classmethod
    def getNodeDataFromName(cls, nodeName):
        ''' Get the data from the node name.
        
        Args:
            nodeName (str)  : The name of the node.
        
        Returns:
            dict            : The node data.
        '''
        # Split the name of the node.
        nodeNameSplit       = nodeName.split('_')
        # Create a dictionary to store the current node data.
        nodeData            = {
            'side'              : [],
            'name'              : [],
            'instanceNumber'    : [],
            'type'              : [],
            'resolution'        : []
        }

        # Determin the template type of each element.
        for i, element in enumerate(nodeNameSplit):
            if(element in ['L', 'R', 'M']):                                 # Check if the element is a side
                nodeData['side'].append(element)
            elif(element.isdigit()):                                        # Check if the element is a number.
                nodeData['instanceNumber'].append(element)
            elif(element in cls.AvailableNodeTypes):                        # Check if the element is a type.    
                nodeData['type'].append(element)
            elif(element in ['low', 'mid', 'high', 'sculpt']):              # Check if the element is a resolution.
                nodeData['resolution'].append(element)
            else:                                                           # Otherwise, the element is the name of the node.
                nodeData['name'].append(element)
        
        # Return the node data.
        return nodeData

    @classmethod
    def isTemplateValid(cls, template):
        ''' Check the template with the available templates.

        Args:
            template    (list)  : A list containing the template.

        Returns:
            bool                : If the template is valid or not.
        '''
        return template in cls.AvailableNameTemplates

    @classmethod
    def hasNonDeformerHistory(cls, node):
        ''' Check if the node has non-deformer history.

        Args:
            node    (str)   : The node to check.

        Returns:
            bool            : True if the node has non-deformer history. False otherwise.
        '''
        # Get the history of the node.
        historyNode         = cmds.listHistory(node, pruneDagObjects=True) or []
        # Get the deform nodes from the history.
        deformHistory       = cmds.ls(historyNode, type="geometryFilter", long=True)
        # Get all the node that are not deform nodes.
        nonDeformHistory    = [node for node in historyNode if(node not in deformHistory)]
        # If there are any non deform nodes, return true.
        if(nonDeformHistory):
            return True
        return False

    @classmethod
    def hasTransform(cls, node):
        ''' Check if the node has a transform.

        Args:
            node (str): The ndoe to check.
        '''
        # Get the world matrix.
        matrix = cmds.xform(node, query=True, matrix=True, worldSpace=True)
        # Check if the matrix is identity.
        return matrix != [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]

    @classmethod
    def isPivotIdentity(cls, node):
        ''' Check if the pivot of a node is at identity.

        Args:
            node    (str)   : The node to check.

        Returns:
            bool            : True if the pivot is at identity. False otherwise.
        '''
        # Remember the selection.
        _sel = cmds.ls(sl=True, long=True)
        # Select the node.
        cmds.select(node, replace=True)

        # Get the translate and orient of the pivot.
        pivotTranslate = cmds.xform(query=True, ws=True, rp=True)
        pivotOrient = cmds.xform(query=True, ws=True, ro=True)

        # Reset the selection.
        cmds.select(_sel, replace=True)

        # Check if the translate and orient are null.
        return pivotTranslate == [0.0, 0.0, 0.0] and pivotOrient == [0.0, 0.0, 0.0]