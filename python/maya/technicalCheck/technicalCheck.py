# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    from    maya            import  cmds

    from    ..mayaAsset     import  MayaAsset

    from    .groupCheck     import  GroupTechnicalCheck
    from    .bufferCheck    import  BufferTechnicalCheck
    from    .meshCheck      import  MeshTechnicalCheck

    VALISATION_CLASSES = [
        GroupTechnicalCheck,
        BufferTechnicalCheck,
        MeshTechnicalCheck
    ]

except:
    pass

class TechnicalCheck():
    ''' Technical Check class.'''

    def __init__(self):
        pass

    @classmethod
    def validateAsset(cls, mayaAsset):
        ''' Perform the validation of an asset.

        Args:
            asset (:class:`MayaAsset`): The asset to validate.

        Returns:
            bool: True if the asset is valid.
        '''
        errors = []
        # Check the hierarchy of the asset.
        if (not cls.validateAssetHierarchy(mayaAsset)):
            # Add the error to the list.
            errors.append({
                'node'      : mayaAsset,
                'errorType' : 'hierarchy'
            })

        # Check if the asset has the same buffers in all resolutions.
        if (not cls.validateAssetBuffers(mayaAsset)):
            # Add the error to the list.
            errors.append({
                'node'      : mayaAsset,
                'errorType' : 'buffers'
            })

        return errors

    @classmethod
    def validateAssetHierarchy(cls, mayaAsset):
        ''' Validate the asset hierarchy.

        Args:
            mayaAsset   (:class:`MayaAsset`)    : The maya asset to check.

        Returns:
            bool                                : True if the check is valid.
        '''
        validationState = True
        # Check the hierarchy.
        if( not mayaAsset.isValid() ):
            validationState = False

        return validationState

    @classmethod
    def validateAssetNodes(cls, nodes):
        ''' Validate the nodes in the asset.

        Args:
            nodes   (list)  : The nodes to validate.

        Returns:
            bool            : True if the check is valid.
        '''
        # Get all the content of the meshes group.
        content = cmds.listRelatives(nodes, allDescendents=True, fullPath=True) or []

        # Create a list to store the errors.
        errors = []

        # Loop though the content.
        for node in content:

            # Get the node shot name without namespace.
            nodeName = node.split('|')[-1].split(':')[-1]

            # Check if the node is a transform.
            if(not cmds.nodeType(node) == 'transform'):
                # It mean the node is a shape.
                # Get the node parent.
                parent = cmds.listRelatives(node, parent=True, fullPath=True)[0]
                # Get the parent node name.
                parentName = parent.split('|')[-1].split(':')[-1]

                # Check if the shape name is correct.
                if(not (nodeName == parentName + 'Shape' or nodeName == parentName + 'ShapeOrig')):
                    errors.append({
                        'node'      : node,
                        'errorType' : 'shapeName'
                    })
                
                continue

            # Get the node end tag.
            nodeEndTag = node.split('_')[-1]
            # If the end tag if a resolution, get the previous tag.
            if(nodeEndTag in ['low', 'mid', 'high']):
                nodeEndTag = node.split('_')[-2]

            # Loop over the validation classes.
            hasValidationClass = False
            for validationClass in VALISATION_CLASSES:
                # Check if the node can be validate by the class.
                if(nodeEndTag in validationClass.getAvailableTypes()):
                    hasValidationClass = True
                    # Validate the name of the node.
                    if(not validationClass.validateName(node)):
                        # Add the error to the list.
                        errors.append({
                            'node'      : node,
                            'errorType' : 'name'
                        })
                    
                    # Validate the content of the node.
                    if(not validationClass.validateContent(node)):
                        # Add the error to the list.
                        errors.append({
                            'node'      : node,
                            'errorType' : 'content'
                        })

                    # Check if the history of the node should be checked.
                    if(validationClass.doCheckHistory()):
                        # Validate the history of the node.
                        if(validationClass.hasNonDeformerHistory(node)):
                            # Add the error to the list.
                            errors.append({
                                'node'      : node,
                                'errorType' : 'history'
                            })
                    
                    # Check if the transform of the node should be checked.
                    if(validationClass.doCheckTransform()):
                        # Validate the transform of the node.
                        if(validationClass.hasTransform(node)):
                            # Add the error to the list.
                            errors.append({
                                'node'      : node,
                                'errorType' : 'transform'
                            })

                    # Check if the pivot of the node should be checked.
                    if(validationClass.doCheckPivot()):
                        # Validate the pivot of the node.
                        if(not validationClass.isPivotIdentity(node)):
                            # Add the error to the list.
                            errors.append({
                                'node'      : node,
                                'errorType' : 'pivot'
                            })
                    break

            if(not hasValidationClass):
                # Add the error to the list.
                errors.append({
                    'node'      : node,
                    'errorType' : 'name'
                })

        return errors

    @classmethod
    def validateAssetBuffers(cls, mayaAsset):
        ''' Validate that the buffers are the same across resolutions.

        Args:
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

        return validationState

    @classmethod
    def logErrors(cls, hooklass, errors):
        ''' Log the errors.

        Args:
            errors  (list)  : The list of errors.
        '''
        # Loop though the errors.
        for error in errors:

            # Generate errors from the error type.
            if (error["errorType"] == "hierarchy"):
                hooklass.logger.error("The hierarchy of {} is not valid.".format(error['node']))
            
            elif (error["errorType"] == "buffers"):
                hooklass.logger.error("The asset {} has different buffers in all resolutions.".format(error['node']))
            
            elif (error["errorType"] == "name"):
                hooklass.logger.error("The name of {} is invalid.".format( error['node'] ))
            
            elif(error["errorType"] == "shapeName"):
                hooklass.logger.error(
                    "The shape name of {} is invalid.".format( error['node'] ))
        
            elif(error["errorType"] == "content"):
                hooklass.logger.error("The content of {} is invalid.".format( error['node'] ))
            
            elif(error["errorType"] == "history"):
                hooklass.logger.error("The node {} has history that should be deleted.".format( error['node'] ))

            elif(error["errorType"] == "transform"):
                hooklass.logger.error(
                    "The node {} has transforms that should be frozen.".format( error['node'] ))

            elif(error["errorType"] == "pivot"):
                hooklass.logger.error(
                    "The pivot of {} is not identity.".format( error['node'] ))
                
            else:
                hooklass.logger.error("An error has been encoutered {}".format(error))

# FIX METHODS
    @classmethod
    def renameShape(cls, shapeNode):
        ''' Rename the shape of the node to correspond to the node name.

        Args:
            shapeNode (str): The shape node to rename.
        '''
        # Get the parent of the shape.
        parent = cmds.listRelatives(shapeNode, parent=True)[0]
        # Get the shot name.
        parent = parent.split('|')[-1]
        # Check if the shape has Orig at the end of its name.
        if(shapeNode.endswith("Orig")):
            # Rename the shape.
            cmds.rename(shapeNode, parent + "Orig")
        else:
            # Rename the shape.
            cmds.rename(shapeNode, parent + "Shape")
        
    @classmethod
    def freezeTransforms(cls, node):
        ''' Freeze the transforms of the node.

        Args:
            node (str): The node to freeze.
        '''
        cmds.makeIdentity(node, apply=True, t=1, r=1, s=1, n=0)
    
    @classmethod
    def makePivotIdentity(cls, node):
        ''' Make the pivot of the node identity.

        Args:
            node (str): The node to make the pivot identity.
        '''
        cmds.xform(node, pivots=(0,0,0), worldSpace=True)