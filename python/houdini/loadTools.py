
# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    import hou
    from tank_vendor    import six

    import sgtk
    import os

except:
    pass

class LoadTools(object):

    def __init__(self):
        pass

    def importAlembicSop(self, name, path, sg_publish_data):
        ''' Import the alembic file in the sop context.

        Args:
            name                (str)   : The entity name.
            path                (str)   : The path to reference.
            sg_publish_data     (dict)  : The shotgrid publish data.

        Return:
            :class:`hou.Node`           : The new node created.
        '''
        # Check if the file exists on disk.
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        # Let houdini create a unique name by incrementing 001 for the imported geometry.
        nodeName = '{}_001'.format(name)

        # Get the geo context.
        obj_context = self.get_current_context("/obj")

        # Create a new geo node.
        try:
            geo_node    = obj_context.createNode("geo", nodeName)
        except hou.OperationFailed:
            # Failed to create the node in this context, create at top-level.
            obj_context = hou.node("/obj")
            geo_node    = obj_context.createNode("geo", nodeName)

        # Delete the default nodes created in the geo.
        for child in geo_node.children():
            child.destroy()

        # Create the alembic node.
        alembic_node = geo_node.createNode("alembic", geo_node.name())
        alembic_node.parm("fileName").set(path)
        alembic_node.parm("reload").pressButton()

        # Show the node.
        self.show_node(alembic_node)

        # Return the new node.
        return alembic_node

    def importMaterialXRop(self, name, path, sg_publish_data):
        ''' Import the materialX file in the rop context.

        Args:
            name                (str)   : The entity name.
            path                (str)   : The path to reference.
            sg_publish_data     (dict)  : The shotgrid publish data.

        Return:
            :class:`hou.Node`           : The new node created.
        '''
        # Check if the file exists on disk.
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        # Let houdini create a unique name by incrementing 001 for the imported geometry.
        nodeName = '{}_001'.format(name)

        # Get the geo context.
        rop_context = self.get_current_context("/out")

        # Create the mtlx node.
        mtlx_node = rop_context.createNode("arnold::materialx", nodeName)
        mtlx_node.parm("selection").set('*')
        mtlx_node.parm("filename").set(path)
        mtlx_node.parm("look").set('default')

        # Show the node.
        self.show_node(mtlx_node)

        # Return the new node.
        return mtlx_node

    @classmethod
    def get_current_context(cls, context_type):
        """Attempts to return the current node context.

        :param str context_type: Return a full context under this context type.
            Example: "/obj"

        Looks for a current network pane tab displaying the supplied context type.
        Returns the full context being displayed in that network editor.

        """

        ''' Get the current context.

        Args:
            context_type    (str)   : The context type.

        Return:
            :class:`hou.Node`       : The current context.
        '''
        # default to the top level context type
        context = hou.node(context_type)

        network_tab = cls.get_current_network_panetab(context_type)
        if(network_tab):
            context = network_tab.pwd()

        return context

    @classmethod
    def get_current_network_panetab(cls, context_type):
        ''' Search for a network pane showing this context.

        Args:
            context_type    (:class:`hou.Node`)     : The context type.

        Returns:
            :class:`hou.ui.paneTab`                 : The current network pane tab.
        '''
        network_tab = None

        # there doesn't seem to be a way to know the current context "type" since
        # there could be multiple network panels open with different contexts
        # displayed. so for now, loop over pane tabs and find a network editor in
        # the specified context type that is the current tab in its pane. hopefully
        # that's the one the user is looking at.
        for panetab in hou.ui.paneTabs():
            if (
                isinstance(panetab, hou.NetworkEditor)
                and panetab.pwd().path().startswith(context_type)
                and panetab.isCurrentTab()
            ):

                network_tab = panetab
                break

        return network_tab

    @classmethod
    def show_node(cls, node):
        ''' Frame the supplied node in the current network pane.

        Args:
            node    (:class:`hou.Node`) : The node to frame in the current network pane.
        '''
        # Get the context from the node path.
        context_type = "/" + node.path().split("/")[0]
        network_tab = cls.get_current_network_panetab(context_type)

        if(not network_tab):
            return

        # Select the node and frame it
        node.setSelected(True, clear_all_selected=True)
        network_tab.cd(node.parent().path())
        network_tab.frameSelection()