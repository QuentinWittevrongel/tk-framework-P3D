try:
    from    maya            import  cmds

    from    .objectCheck    import  ObjectTechnicalCheck
except:
    pass

class BufferTechnicalCheck(ObjectTechnicalCheck):

    # Define the templates that the nodes can have.
    AVAILABLE_NAME_TEMPLATES   = [
        [           '{NODE_NAME}',                          '{TYPE}'],
        [           '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}'],
        ['{SIDE}',  '{NODE_NAME}',                          '{TYPE}'],
        ['{SIDE}',  '{NODE_NAME}',  '{INSTANCE_NUMBER}',    '{TYPE}']
    ]

    # Define the types of the node can have.
    AVAILABLE_TYPES = [
        'BUF'
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
        # Check if the node has children.
        if(not content):
            return True

        # Check if the ndoe only contains transform nodes.
        for child in content:
            if(cmds.nodeType(child) != 'transform'):
                return False

        # No error found, return True.
        return True
    
