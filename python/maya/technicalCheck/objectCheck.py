try:
    from    maya            import  cmds
except:
    pass

class ObjectTechnicalCheck:
    ''' Base class for technical check.'''

    # Define the templates that the nodes can have.
    AVAILABLE_NAME_TEMPLATES   = []

    # Define the types of the node can have.
    AVAILABLE_TYPES = []

    def __init__(self, node):
        ''' Init the class.

        Args:
            node (str): The path to the node.
        '''
        self._node = node
    
    @classmethod
    def getAvailableNameTemplates(cls):
        ''' Get the available name templates.

        Returns:
            list: The available name templates.
        '''
        return cls.AVAILABLE_NAME_TEMPLATES

    @classmethod
    def getAvailableTypes(cls):
        ''' Get the available types.

        Returns:
            list: The available types.
        '''
        return cls.AVAILABLE_TYPES

    @classmethod
    def getTemplateParts(cls):
        ''' Get the template parts.

        Returns:
            dict: The template parts.
        '''
        # Define the template parts.
        TEMPLATE_PARTS = {
            '{INSTANCE_NUMBER}'   : {
                'type'      : 'int',
            },
            '{SIDE}'              : {
                'type'      : 'string',
                'values'    : ['L', 'R', 'M'],
            },
            '{TYPE}'              : {
                'type'      : 'string',
                'values'    : cls.AVAILABLE_TYPES,
            },
            '{RESOLUTION}'        : {
                'type'      : 'string',
                'values'    : ['low', 'mid', 'high'],
            },
            '{NODE_NAME}'         : {
                'type'      : 'string',
            }
        }
        return TEMPLATE_PARTS

    @classmethod
    def doCheckHistory(cls):
        ''' Say the node to perform the history check.

        Returns:
            bool: True if the node should perform the history check.
        '''
        return False

    @classmethod
    def doCheckTransform(cls):
        ''' Say the node to perform the transform check.

        Returns:
            bool: True if the node should perform the transform check.
        '''
        return False

    @classmethod
    def doCheckPivot(cls):
        ''' Say the node to perform the pivot check.

        Returns:
            bool: True if the node should perform the pivot check.
        '''
        return False

    @classmethod
    def validateContent(cls, node):
        ''' Validate the content of the node.

        Args:
            node (str): The path to the node.

        Returns:
            bool: True if the content is valid.
        '''
        raise NotImplementedError

    @classmethod
    def validateName(cls, node):
        ''' Validate the name of the node.

        Args:
            node (str): The path to the node.

        Returns:
            bool: True if the name is valid.
        '''
        # Get the last part of the node.
        nodeName = node.split('|')[-1]
        # Remove the namespace.
        nodeName = nodeName.split(':')[-1]

        # Get the template from the node name.
        template = cls.getTemplateFromName(nodeName)

        # Check if the template is valid.
        if(not template):
            return False
        # Check if the template is valid.
        availableTemplates = cls.getAvailableNameTemplates()

        if(not template in availableTemplates):
            return False
        return True

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
        # get the template parts.
        templateParts       = cls.getTemplateParts()

        for i, element in enumerate(nodeNameSplit):

            # Loop over the template parts.
            for partName, partValue in templateParts.items():

                # Check if the value key exists.
                values = partValue.get('values', None)
                if(values):
                    # Check if the element is in the values.
                    if(element in values):
                        # Set the template part.
                        template[i] = partName
                        break
                    continue
                
                # Get the type of the template part.
                partType = partValue.get('type', None)
                if(partType == 'string'):
                    # Check if the element is not a number.
                    if(not element.isdigit()):
                        # Set the template part.
                        template[i] = partName
                        break
                elif(partType == 'int'):
                    # Check if the element is a number.
                    if(element.isdigit()):
                        # Check if the number is formated with 3 digits.
                        if(len(element) == 3):
                            # Set the template part.
                            template[i] = partName
                            break
                
                # If the element is not in the values, then it is not a valid template.
                template[i] = '{UNDEFINED}'
        
        # Return the node template.
        return template

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