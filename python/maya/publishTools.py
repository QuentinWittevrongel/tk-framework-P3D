
# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    from maya import cmds
    from maya import mel
except:
    pass

__ABC_COMMAND_WORLD__       = 'AbcExport -j "-frameRange <startFrame> <endFrame> -noNormals -ro -stripNamespaces -uvWrite -worldSpace -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'
__ABC_COMMAND_LOCAL__       = 'AbcExport -j "-frameRange <startFrame> <endFrame> -noNormals -ro -stripNamespaces -uvWrite -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'
__ABC2_COMMAND_WORLD__      = 'AbcExport2 -j "-frameRange <startFrame> <endFrame> -noNormals -ro -stripNamespaces -uvWrite -worldSpace -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'
__ABC2_COMMAND_LOCAL__      = 'AbcExport2 -j "-frameRange <startFrame> <endFrame> -noNormals -ro -stripNamespaces -uvWrite -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'

class PublishTools(object):

    def __init__(self):
        pass
    
    def getSceneFrameRange(self):
        ''' Get the start and the end frame of the timeline.
        
        Returns:
            tuple(int, int) : The start and end frame.
        '''
        startFrame  = cmds.playbackOptions(q=True, min=True)
        endFrame    = cmds.playbackOptions(q=True, max=True)

        return startFrame, endFrame

    def loadABCExport2Plugin(self):
        """ Load the alembic 2 plugin.
        """
        cmds.loadPlugin('AbcExport2')

    def loadABCExportPlugin(self):
        """ Load the alembic 2 plugin.
        """
        cmds.loadPlugin('AbcExport')

    def exportAlembic(self, meshes, startFrame, endFrame, filePath, exportABCVersion=1, spaceType="world"):
        ''' Export the list of meshes in an alembic file.

        Args:
            meshes              (list(str)):    The list of meshes to export.
            startFrame          (int):          The first frame of the export.
            endFrame            (int):          The last frame of the export.
            filePath            (str):          The full path to export the alembic.
            exportABCVersion    (int):          The version of the alembic plugin.
            spaceType           (str):          The space use to export the alembic.
        '''
        abcCommand = ""
        # Load the abc export plugin and select the command to export.
        if(exportABCVersion == 1):
            self.loadABCExportPlugin()
            if(spaceType == "world"):
                abcCommand = __ABC_COMMAND_WORLD__
            else:
                abcCommand = __ABC_COMMAND_LOCAL__
        elif(exportABCVersion == 2):
            self.loadABCExport2Plugin()
            if(spaceType == "world"):
                abcCommand = __ABC2_COMMAND_WORLD__
            else:
                abcCommand = __ABC2_COMMAND_LOCAL__

        # Replace the command tags.
        abcCommand = abcCommand.replace("<startFrame>", str(startFrame))
        abcCommand = abcCommand.replace("<endFrame>", str(endFrame))
        abcCommand = abcCommand.replace("<listObjects>", ' -root '.join(meshes))
        abcCommand = abcCommand.replace("<filePath>", filePath.replace("\\", "/"))

        # Launch the command.
        mel.eval(abcCommand)