try:
    from    maya            import  cmds

    from    .objectCheck    import  ObjectTechnicalCheck
except:
    pass

class MeshTechnicalCheck(ObjectTechnicalCheck):

    # Define the templates that the nodes can have.
    AVAILABLE_NAME_TEMPLATES   = [
        [           '{NODE_NAME}',                          '{TYPE}',   '{RESOLUTION}'  ],
        [           '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}',   '{RESOLUTION}'  ],
        ['{SIDE}',  '{NODE_NAME}',                          '{TYPE}',   '{RESOLUTION}'  ],
        ['{SIDE}',  '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}',   '{RESOLUTION}'  ]
    ]

    # Define the types of the node can have.
    AVAILABLE_TYPES = [
        'MSH'
    ]
    
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
        # Get the content of the node.
        content = cmds.listRelatives(node, children=True, fullPath=True) or []
        # Return False if the node does not have children.
        if(not content):
            return False
        
        # # Return False if the node has more than 2 children.
        # if(len(content) > 2):
        #     return False

        # Check if all the content is a mesh.
        fullMesh = all([cmds.nodeType(child) == 'mesh' for child in content])
        # Check if all the content is a nurbsCurve.
        fullCurve = all([cmds.nodeType(child) == 'nurbsCurve' for child in content])

        if(not (fullMesh or fullCurve)):
            return False
        
        return True

