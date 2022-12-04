
# Try to import maya module to avoid error when the module is loaded outside of maya.
try:
    from maya           import cmds
    from maya           import mel
    from mtoa.core      import createStandIn

    from tank_vendor    import six

    import sgtk
    import os
    import re

except:
    pass

__ABC_COMMAND_WORLD__       = 'AbcExport -j "-frameRange <startFrame> <endFrame> -noNormals -renderableOnly <stripNamespaces> -uvWrite -worldSpace -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'
__ABC_COMMAND_LOCAL__       = 'AbcExport -j "-frameRange <startFrame> <endFrame> -noNormals -renderableOnly <stripNamespaces> -uvWrite -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'
__ABC2_COMMAND_WORLD__      = 'AbcExport2 -j "-frameRange <startFrame> <endFrame> -noNormals -renderableOnly <stripNamespaces> -uvWrite -worldSpace -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'
__ABC2_COMMAND_LOCAL__      = 'AbcExport2 -j "-frameRange <startFrame> <endFrame> -noNormals -renderableOnly <stripNamespaces> -uvWrite -writeVisibility -writeUVSets -dataFormat ogawa -root <listObjects> -file <filePath>"'

class PublishTools(object):
    ''' Commun publish functions for Maya.'''

    def __init__(self):
        pass

    # Get functions.

    def getSceneFrameRange(self):
        ''' Get the start and the end frame of the timeline.
        
        Returns:
            tuple(int, int) : The start and end frame.
        '''
        startFrame  = cmds.playbackOptions(q=True, min=True)
        endFrame    = cmds.playbackOptions(q=True, max=True)

        return startFrame, endFrame

    def getCurrentSessionPath(self, hookClass):
        """
        Return the path to the current session
        :return:
        """
        path = cmds.file(query=True, sn=True)

        if path is not None:
            path = six.ensure_str(path)

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Maya session has not been saved."
            hookClass.logger.error(error_msg)
            raise Exception(error_msg)

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)
        hookClass.logger.info("Path : %s" % path)

        return path

    def getWorkTemplateFieldsFromPath(self, hookClass, workTemplate, path, addFields=None):

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = workTemplate.get_fields(path)
        hookClass.logger.info("Work Fields : %s" % work_fields)

        # Add Custom fields.
        if(addFields):
            work_fields.update(addFields)

        # ensure the fields work for the publish template
        missing_keys = workTemplate.missing_keys(work_fields)
        if missing_keys:
            error_msg = (
                "Work file '%s' missing keys required for the "
                "publish template: %s" % (path, missing_keys)
            )
            hookClass.logger.error(error_msg)
            raise Exception(error_msg)
        
        return work_fields

    # Load functions.

    def loadABCExportPlugin(self):
        """ Load the alembic 2 plugin.
        """
        cmds.loadPlugin('AbcExport')

    def loadABCExport2Plugin(self):
        """ Load the alembic 2 plugin.
        """
        cmds.loadPlugin('AbcExport2')

    # Export functions.

    def exportMayaSelection(self, selection, path):
        ''' Save the selection as maya scene.

        Args:
            selection   (list(str)):   The selection to save in the maya file.
            path        (str):          The path to save the maya file.
        '''
        # Select the asset before save.
        cmds.select(clear=True)
        cmds.select(selection)

        # Save the asset.
        cmds.file(path, force=True, type="mayaAscii", exportSelected=True, preserveReferences=True)

    def exportMayaAsset(self, asset, path):
        ''' Save the asset as maya scene.

        Args:
            asset   (:class:`MayaAsset`):   The asset to save in the maya file.
            path    (str):                  The path to save the maya file.
        '''
        self.exportMayaSelection(asset.fullname, path)

    def exportMayaAssetRig(self, asset, filePath):
        ''' Export the asset rig as a maya ascii file.

        Args:
            asset       (:class:`MayaAsset`)    : The asset to export.
            filePath    (str)                   : The full path to export the maya file.
        '''
        # Make the additional connections. For instance the facial rig.

        # Import all the references of the asset.
        asset.importChildReferences()

        # Bake the namespaces.
        asset.freezeNamespace()

        # Select the asset.
        cmds.select(asset.fullname, replace=True)

        # Export the meshes.
        cmds.file(filePath, force=True, options="v=0", typ="mayaAscii", exportSelected=True, preserveReferences=False)

    def exportMayaEnvironment(self, environment, path):
        ''' Export the environment as a maya ascii file.

        Args:
            environment (:class:`MayaEnvironment`)  : The environment to export.
            path        (str)                       : The full path to export the maya file.
        '''
        self.exportMayaSelection(environment.fullname, path)

    def exportAlembic(self, meshes, startFrame, endFrame, filePath, exportABCVersion=1, spaceType="world", stripNamespace=True):
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

        # Optionnaly enable strip namespace.
        if(stripNamespace):
            abcCommand.replace("<stripNamespaces>", "-stripNamespaces")
        else:
            abcCommand.replace("<stripNamespaces>", "")

        # Replace the command tags.
        abcCommand = abcCommand.replace("<startFrame>", str(startFrame))
        abcCommand = abcCommand.replace("<endFrame>", str(endFrame))
        abcCommand = abcCommand.replace("<listObjects>", ' -root '.join(meshes))
        abcCommand = abcCommand.replace("<filePath>", filePath.replace("\\", "/"))

        # Launch the command.
        mel.eval(abcCommand)

    def exportMaterialX(self, asset, lookName, path, lod):
        ''' Publish a material X for asset.

        Args:
            asset       (:class:`MayaObject`)   : The asset from publish the material X.
            lookName    (str)                   : The name of the look.
            path        (str)                   : The path to save the material X.
            lod         (str)                   : The level of detail of the asset to publish material X.
        '''
        # Get the list of asset's meshes.
        meshes = None
        if(lod == "LO"):
            meshes = asset.meshesLO
        elif(lod == "MI"):
            meshes = asset.meshesMI
        elif(lod == "HI"):
            meshes = asset.meshesHI

        # Get the asset namespace.
        assetNamespace = asset.rootNamespace

        # If meshes in the lod group we can publish the material X for this lod.
        if(meshes):
            # Loop over the meshes together the shapes that will be present in the material X file.
            # We do that to fix the object path in the material X file to be sure that is compatible with the alembic path.
            shapeMeshes = {}
            for msh in meshes:
                mshName = msh.split("|")[-1]
                shapes = [shape for shape in cmds.listRelatives(msh, allDescendents=True, fullPath=True)
                            if cmds.nodeType(shape) == "mesh" and
                            cmds.getAttr("%s.intermediateObject" % shape) == 0]
                if(len(shapes) > 0):
                    for shape in shapes:
                        print(shape)
                        shapeName = shape.split("|")[-1]
                        # We build the correct path to replace it in the material X file.
                        localPath = "|%s%s" % (mshName, shape.split(msh)[-1])
                        # Clean the namespace in the path hierarchy.
                        if(assetNamespace):
                            localPath = localPath.replace("%s:" % assetNamespace, "")
                        # Replace the path separator | by /
                        localPath = localPath.replace("|", "/")
                        print(localPath)
                        print(shapeName)
                        # Add the fixed path to the shapes dictionary.
                        shapeMeshes[shapeName] = localPath
            # Export the material X.
            cmds.arnoldExportToMaterialX(meshes, filename=path, look=lookName, fullPath=0, materialExport=0, relative=1, separator="/")
            # Fix the meshes path in the alembic file.
            self.fixMaterialXGeometryPath(path, shapeMeshes)

    # Generic Accept functions.

    def checkPublishTemplate(self, hookClass, template_name):
        ''' Check if the publish template is defined and valid.

        Args:
            hookClass       (:class:`HookClass`):   The hook plugin class.
            template_name   (str):                  The publish template.

        Returns:
            bool: True is valid, otherwise False.
        '''
        publisher = hookClass.parent
        # ensure the publish template is defined and valid.
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            hookClass.logger.debug(
                "The valid publish template could not be determined for the "
                "session geometry item. Not accepting the item."
            )
            return False, None
        
        return True, publish_template

    def hookPublishAccept(self, hookClass, settings, item, publishTemplate, propertiesPublishTemplate, isChild=False):
        ''' Generic implementation of the accept method for the publish plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
            publishTemplate             (str):      The plugin publish template name.
            propertiesPublishTemplate   (str) :     The publish template name for item properties.

        Returns:
            dict : dictionary with boolean keys accepted, required and enabled
        '''
        accepted = True
        # Get the publish plugin publish template.
        # This template is assgin in config.env.includes.settings.tk-multi-publish2.yml
        template_name = settings[publishTemplate].value
        # Check if the template is valid.
        accepted, publish_template = self.checkPublishTemplate(hookClass, template_name)
        # we've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties[propertiesPublishTemplate] = publish_template
        # because a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        item.context_change_allowed = False

        return {"accepted": accepted, "checked": True}
    
    def hookPublishAcceptLOD(self, hookClass, settings, item, publishTemplate, propertiesPublishTemplate, lod):
        ''' Generic implementation of the accept method for the publish asset LOD plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
            publishTemplate             (str):      The plugin publish template name.
            propertiesPublishTemplate   (str) :     The publish template name for item properties.

        Returns:
            dict : dictionary with boolean keys accepted, required and enabled
        '''
        # Execute the genenic accept method.
        dict_ = self.hookPublishAccept(
            hookClass,
            settings, 
            item,
            publishTemplate,
            propertiesPublishTemplate,
        )
        accepted = dict_["accepted"]

        # We use the MayaAsset class stored in the item to check if the current asset is a valid asset.
        mayaAsset = item.parent.properties.get("assetObject")

        meshes = []
        if(lod == "LO"):
            meshes = mayaAsset.meshesLO
        elif(lod == "MI"):
            meshes = mayaAsset.meshesMI
        elif(lod == "HI"):
            meshes = mayaAsset.meshesHI

        if(len(meshes) == 0):
            hookClass.logger.debug("The %s group is empty." % lod)
            accepted = False

        return {"accepted": accepted, "checked": True}

    # Generic Validate functions.

    def addPublishDatasToPublishItem(self, hookClass, item, publishTemplateName, addFields=None):

        # Get the session path.
        sessionPath = self.getCurrentSessionPath(hookClass)

        # Use the working template to extract fields from sessionPath to solve the template path.
        workTemplate = item.properties.get("work_template")
        if not(workTemplate):
            workTemplate = item.parent.properties.get("work_template")

        workFields = self.getWorkTemplateFieldsFromPath(hookClass, workTemplate, sessionPath, addFields)

        # Get the template path.
        publishTemplate = item.properties.get(publishTemplateName)

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.
        path = publishTemplate.apply_fields(workFields)
        item.properties["path"]         = sgtk.util.ShotgunPath.normalize(path)
        item.properties["publish_path"] = item.properties["path"]

        # use the work file's version number when publishing
        if "version" in workFields:
            item.properties["publish_version"] = workFields["version"]

        print(item.properties["path"])
        print(item.properties["publish_path"])

        return item

    def hookPublishValidate(self, hookClass, settings, item, propertiesPublishTemplate, isChild=False, addFields={}):
        ''' Generic implementation of the validate method for the publish plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # We use the MayaAsset class stored in the item to check if the current asset is a valid asset.
        if(isChild):
            mayaAsset = item.parent.properties.get("assetObject")
        else:
            mayaAsset = item.properties.get("assetObject")

        # Check if the asset root is a valid asset.
        if not (mayaAsset.isValid()):
            error_msg = "The asset %s is not a valid. Please check the asset group structure."
            hookClass.logger.error(error_msg)
            raise Exception(error_msg)

        # Add the publish path datas to the publish item.
        # That allow us to reuse the datas for the publish.
        self.addPublishDatasToPublishItem(hookClass, item, propertiesPublishTemplate, addFields)

    # Asset Publish functions.

    def hookPublishMayaScenePublish(self, hookClass, settings, item, isChild=False):
        ''' Generic implementation of the publish method for maya scene publish plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the item asset object.
        if(isChild):
            mayaObject = item.parent.properties["assetObject"]
        else:
            mayaObject = item.properties["assetObject"]

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        self.exportMayaAsset(mayaObject, publish_path)
    
    def hookPublishMayaSceneLODPublish(self, hookClass, settings, item, lod, isChild=False):
        ''' Generic implementation of the publish method for maya scene publish asset LOD plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the item asset object.
        if(isChild):
            asset = item.parent.properties["assetObject"]
        else:
            asset = item.properties["assetObject"]

        # Delete the meshes lod that we don't need.
        if(lod == "LO"):
            asset.deleteMeshesMI()
            asset.deleteMeshesHI()
        elif(lod == "MI"):
            asset.deleteMeshesLO()
            asset.deleteMeshesHI()
        elif(lod == "HI"):
            asset.deleteMeshesLO()
            asset.deleteMeshesMI()

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        self.exportMayaAsset(asset, publish_path)

        # Reload the master scene.
        path = cmds.file(query=True, sn=True)
        cmds.file(path, force=True, open=True)

    # Asset Rig Publish functions.

    def hookPublishMayaRigPublish(self, hookClass, settings, item, isChild=False):
        ''' Generic implementation of the publish method for maya scene publish plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the item asset object.
        if(isChild):
            asset = item.parent.properties["assetObject"]
        else:
            asset = item.properties["assetObject"]

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        # Pubish the asset rig.
        self.exportMayaAssetRig(asset, publish_path)

        # As there are modifications between the working file and the published file.
        # Reload the master scene.
        path = cmds.file(query=True, sn=True)
        cmds.file(path, force=True, open=True)

    def hookPublishMayaRigLODPublish(self, hookClass, settings, item, lod, isChild=False):
        ''' Generic implementation of the publish method for maya scene publish asset LOD plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the item asset object.
        if(isChild):
            asset = item.parent.properties["assetObject"]
        else:
            asset = item.properties["assetObject"]

        # Delete the meshes lod that we don't need.
        if(lod == "LO"):
            asset.deleteMeshesMI()
            asset.deleteMeshesHI()
        elif(lod == "MI"):
            asset.deleteMeshesLO()
            asset.deleteMeshesHI()
        elif(lod == "HI"):
            asset.deleteMeshesLO()
            asset.deleteMeshesMI()

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        # Pubish the asset rig.
        self.exportMayaAssetRig(asset, publish_path)

        # As there are modifications between the working file and the published file.
        # Reload the master scene.
        path = cmds.file(query=True, sn=True)
        cmds.file(path, force=True, open=True)

    # Asset Alembic Publish functions.

    def hookPublishAlembicLODPublish(self, hookClass, settings, item, lod, useFrameRange=False, isChild=False):
        ''' Generic implementation of the publish method for alembic publish asset LOD plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the maya asset stored in the ui item.
        if(isChild is True):
            asset = item.parent.properties.get("assetObject")
        else:
            asset = item.properties.get("assetObject")

        # Get the asset's meshes to export.
        if(lod == "LO"):
            # Remove the LOD specification of the meshes.
            content = cmds.listRelatives(asset.groupMeshesLO, allDescendents=True, fullPath=True, type="transform")
            content.sort(key = lambda x : len(x.split('|')) , reverse = True)
            for transform in content:
                # Get the shortname.
                shortName = transform.split("|")[-1]
                # Remove the lod specification.
                newName = shortName.replace("_low", "")
                cmds.rename(transform, newName)

            meshes = asset.meshesLO
        elif(lod == "MI"):
            # Remove the LOD specification of the meshes.
            content = cmds.listRelatives(asset.groupMeshesMI, allDescendents=True, fullPath=True, type="transform")
            content.sort(key = lambda x : len(x.split('|')) , reverse = True)
            for transform in content:
                # Get the shortname.
                shortName = transform.split("|")[-1]
                # Remove the lod specification.
                newName = shortName.replace("_mid", "")
                cmds.rename(transform, newName)

            meshes = asset.meshesMI
        elif(lod == "HI"):
            # Remove the LOD specification of the meshes.
            content = cmds.listRelatives(asset.groupMeshesHI, allDescendents=True, fullPath=True, type="transform")
            content.sort(key = lambda x : len(x.split('|')) , reverse = True)
            for transform in content:
                # Get the shortname.
                shortName = transform.split("|")[-1]
                # Remove the lod specification.
                newName = shortName.replace("_high", "")
                cmds.rename(transform, newName)

            meshes = asset.meshesHI

        if(useFrameRange):
            # Get the scene start and end frame.
            startFrame, endFrame = self.getSceneFrameRange()
        else:
            startFrame = 1
            endFrame = 1

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        # Export the asset's meshes in alembic path.
        self.exportAlembic(
            meshes,
            startFrame,
            endFrame,
            publish_path,
            exportABCVersion=2,
            spaceType="local"
        )

        # As there are modifications between the working file and the published file.
        # Reload the master scene.
        path = cmds.file(query=True, sn=True)
        cmds.file(path, force=True, open=True)

    # MaterialX Publish functions.

    def hookPublishMaterialXLODPublish(self, hookClass, settings, item, lod, isChild=False):
        ''' Generic implementation of the publish method for maya scene publish plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the item asset object.
        if(isChild):
            asset = item.parent.properties["assetObject"]
        else:
            asset = item.properties["assetObject"]

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        self.exportMaterialX(asset, "default", publish_path, lod)

    # Environment Publish functions.
    def hookPublishMayaEnvironmentPublish(self, hookClass, settings, item, isChild=False):
        ''' Generic implementation of the publish method for maya environment publish plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the item maya object.
        if(isChild):
            mayaObject = item.parent.properties["mayaObject"]
        else:
            mayaObject = item.properties["mayaObject"]

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        self.exportMayaEnvironment(mayaObject, publish_path)

    # Environment Alembic Publish functions.
    def hookPublishAlembicEnvironmentPublish(self, hookClass, settings, item, useFrameRange=False, isChild=False):
        ''' Generic implementation of the publish method for alembic publish environment plugin hook.

        Args:
            settings                    (dict):     The keys are strings, matching
                                                    the keys returned in the settings property. The values are `Setting`
                                                    instances.
            item                        (sgUIItem): Item to process
        '''
        # Get the item maya object.
        if(isChild):
            mayaObject = item.parent.properties["mayaObject"]
        else:
            mayaObject = item.properties["mayaObject"]

        if(useFrameRange):
            # Get the scene start and end frame.
            startFrame, endFrame = self.getSceneFrameRange()
        else:
            startFrame = 1
            endFrame = 1

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        # Get the environment's asset's main buffers.
        meshes = mayaObject.getAllAssetsMainBuffers()

        # Export the buffers as alembic.
        self.exportAlembic(
            meshes,
            startFrame,
            endFrame,
            publish_path,
            exportABCVersion=2,
            spaceType="local",
            stripNamespace=False
        )

    # Post Publish functions.

    def cleanLineNameSpace(self, line):
        ''' Clean the namespace for the object or shader name.

        Args:
            line (str): The line to clean.
        '''
        newLine = line
        matchs = re.findall(r'\"(.*?)\"', newLine)
        # Check if we find some pattern like "..."
        if(matchs):
            # Loop over the patterns.
            for match in matchs:
                # Check if the patterns contain : but not :/
                if(match.find(":") != -1 and match.find(":/") == -1):
                    # Check if the pattern is a object path.
                    if(match.find("/") != -1):
                        # If path, split the object name to remove the namespace.
                        splitPath       = match.split("/")
                        objects         = []
                        # Remove the name space for each object in the pattern path.
                        for obj in splitPath:
                            if(obj.find(":") != -1):
                                splitNameSpace = obj.split(":")
                                objects.append(splitNameSpace[1])
                            else:
                                objects.append(obj)
                        # Rebuild the object path.
                        newPath = '/'.join(objects)
                        # Fix the line.
                        newLine = newLine.replace(match, newPath)
                    else:
                        # Split the name space.
                        splitNameSpace = match.split(":")
                        # Fix the line.
                        newLine = newLine.replace(match, splitNameSpace[1])

        return newLine

    def fixMaterialXGeometryPath(self, filePath, listMeshes):
        ''' Fix the assign geometry path to match the alembic path.

        Args:
            filePath (str): The path of the material X.
        '''
        print("CLEAN MATERIAL X MESHES PATH TO MATCH ALAMBIC.")

        lines = None

        with open(filePath, 'r') as f:
            lines = f.readlines() 

        for index, line in enumerate(lines):
            if(line.find("geom=") != -1):
                match = re.search(r'geom=\"(.*?)\"', line)
                if(match):
                    print(match.group(1))
                    mesheShape = match.group(1).split("/")[-1].split(":")[-1]
                    print(mesheShape)
                    if(mesheShape in listMeshes):
                        line = line.replace(match.group(1), listMeshes[mesheShape])
            
            line = self.cleanLineNameSpace(line)

            lines[index] = line

        with open(filePath, 'w') as f:
            f.writelines(lines) 

    # Reviews.

    def hookUploadReviewValidate(self, hookClass, settings, item):
        ''' Generic implementation of the upload method for a review file validate plugin hook.

        Args:
            hookClass   (:class:)                   : The hook instance.
            settings    (:class:`PluginSetting`)    : The settings for the plugin.
            item        (:class:`PublishItem`)      : The item to process.
        '''
        # Get the file path to the review file.
        filePath = item.properties.get("path")

        # Check if the file exist.
        if(not os.path.exists(filePath)):
            error_msg = "The file {} does not exist.".format(filePath)
            hookClass.logger.error(error_msg)
            raise Exception(error_msg)

    def hookUploadReviewPublish(self, hookClass, settings, item):
        ''' Generic implementation of the upload method for a review file publish plugin hook.

        Args:
            hookClass   (:class:)                   : The hook instance.
            settings    (:class:`PluginSetting`)    : The settings for the plugin.
            item        (:class:`PublishItem`)      : The item to process.
        '''
        # Get the publisher.
        publisher       = hookClass.parent
        # Get the publish path.
        path            = item.properties["path"]

        # Get the file name as the version name.
        pathComponents  = publisher.util.get_file_path_components(path)
        publishName     = pathComponents["filename"]        
        hookClass.logger.debug("Publish name: {0}".format(publishName))

        # Create the version data.
        hookClass.logger.info("Creating Version...")
        versionData = {
            "project"           : item.context.project,
            "code"              : publishName,
            "description"       : item.description,
            "entity"            : hookClass._getVersionEntity(item),
            "sg_task"           : item.context.task,
            "sg_path_to_movie"  : path
        }

        # Create the version.
        version = publisher.shotgun.create("Version", versionData)
        hookClass.logger.info("Version created!")

        # Stash the version info in the item just in case
        item.properties["sg_version_data"] = version

        # Upload the movie to shotgrid.
        hookClass.logger.info("Uploading content...")

        # On windows, ensure the path is utf-8 encoded to avoid issues with the shotgun api.
        if(sgtk.util.is_windows()):
            uploadPath = six.ensure_text(path)
        else:
            uploadPath = path

        # Upload the movie on shotgrid.
        hookClass.parent.shotgun.upload(
            "Version", version["id"], uploadPath, "sg_uploaded_movie"
        )

        # Log for the user.
        hookClass.logger.info("Upload complete!")

    def hookUploadReviewFinalize(self, hookClass, settings, item):
        ''' Generic implementation of the upload method for a review file finalize plugin hook.

        Args:
            hookClass   (:class:)                   : The hook instance.
            settings    (:class:`PluginSetting`)    : The settings for the plugin.
            item        (:class:`PublishItem`)      : The item to process.
        '''
        # Retrieve data from the properties.
        path        = item.properties["path"]
        version     = item.properties["sg_version_data"]
        # Add a logger info to show version on shotgrid.
        hookClass.logger.info(
            'Version uploaded for file: {0}.'.format(path),
            extra={
                "action_show_in_shotgun": {
                    "label"     : "Show Version",
                    "tooltip"   : "Reveal the version in ShotGrid.",
                    "entity"    : version,
                }
            },
        )