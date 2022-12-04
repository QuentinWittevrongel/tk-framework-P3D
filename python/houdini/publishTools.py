# Try to import hou module to avoid error when the module is loaded outside of Houdini.
try:
    import  hou

    from    tank_vendor     import six

    import  sgtk
    import  os
    import  re

except:
    pass

class PublishTools(object):
    ''' Commun publish functions for Houdini.'''

    def __init__(self):
        pass

    # Get functions.

    def getCurrentSessionPath(self, hookClass):
        ''' Get the current session path.
        
        Args:
            hookClass   (:class:`PublishTask`)  : The hook plugin class.
        
        Returns:
            str                                 : The current session path.
        '''
        path = hou.hipFile.path()

        if(path is not None):
            path = six.ensure_str(path)

        if(path == "untitled.hip"):
            # The session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Houdini session has not been saved."
            hookClass.logger.error(error_msg)
            raise Exception(error_msg)

        # Get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)
        hookClass.logger.info("Path : %s" % path)

        return path

    def getWorkTemplateFieldsFromPath(self, hookClass, workTemplate, path, addFields=None):
        ''' Get the work template fields from the path and add fields.
        
        Args:
            hookClass       (:class:`PublishTask`)              : The hook plugin class.
            workTemplate    (:class:`Template`)                 : The work template.
            path            (str)                               : The path to get the fields from.
            addFields       (dict,  optional)                   : The fields to add to the work template fields.
                                                                Defaults to None.

        Returns:
            dict                                                : The work template fields.
        '''
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

    # Accept functions.

    def checkPublishTemplate(self, hookClass, template_name):
        ''' Check if the publish template is defined and valid.

        Args:
            hookClass       (:class:`PublishTask`)  : The hook plugin class.
            template_name   (str)                   : The publish template.

        Returns:
            tuple(bool, :class:`Template`)          : The tuple with the boolean accept and the template.
        '''
        publisher = hookClass.parent
        # Ensure the publish template is defined and valid and that we also have
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
            settings                    (:class:`PluginSetting`)    : The keys are strings, matching the keys returned
                                                                    in the settings property. The values are `Setting`
                                                                    instances.
            item                        (:class:`PublishItem`)      : Item to process
            publishTemplate             (str)                       : The plugin publish template name.
            propertiesPublishTemplate   (str)                       : The publish template name for item properties.
            isChild                     (bool,  optional)           : True if the item is a child, otherwise False.
                                                                    Defaults to False.

        Returns:
            dict                                                    : Dictionary with boolean keys accepted,
                                                                    required and enabled.
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

    # Validate functions.

    def addPublishDatasToPublishItem(self, hookClass, item, publishTemplateName, addFields=None):
        ''' Add the publish path datas to the publish item.
        
        Args:
            hookClass               (:class:`PublishTask`)  : The hook plugin class.
            item                    (:class:`PublishItem`)  : The publish item.
            publishTemplateName     (str)                   : The publish template name.
            addFields               (dict,  optional)       : The fields to add to the publish template fields.
                                                            Defaults to None.

        Returns:
            :class:`PublishItem`                            : The publish item.
        '''
        # Get the session path.
        sessionPath = self.getCurrentSessionPath(hookClass)

        # Use the working template to extract fields from sessionPath to solve the template path.
        workTemplate = item.properties.get("work_template")
        if (not workTemplate):
            workTemplate = item.parent.properties.get("work_template")

        # Get the work fields.
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
        if("version" in workFields):
            item.properties["publish_version"] = workFields["version"]

        return item

    def hookPublishValidate(self, hookClass, settings, item, propertiesPublishTemplate, isChild=False, addFields={}):
        ''' Generic implementation of the validate method for the publish plugin hook.

        Args:
            hookClass                   (:class:`PublishTask`)      : The hook plugin class.
            settings                    (:class:`PluginSetting`)    : The keys are strings, matching the keys returned
                                                                    in the settings property. The values are `Setting`
                                                                    instances.
            item                        (:class:`PublishItem`)      : Item to process
            propertiesPublishTemplate   (str)                       : The publish template name for item properties.
            isChild                     (bool,  optional)           : True if the item is a child, otherwise False.
                                                                    Defaults to False.
            addFields                   (dict,  optional)           : The fields to add to the publish template fields.
                                                                    Defaults to {}.
        '''

        # Add the publish path datas to the publish item.
        # That allow us to reuse the datas for the publish.
        self.addPublishDatasToPublishItem(hookClass, item, propertiesPublishTemplate, addFields)

    # MaterialX Publish functions.

    def hookPublishMaterialXPublish(self, hookClass, settings, item, isChild=False):
        ''' Generic implementation of the validate method for the materialX publish plugin hook.

        Args:
            hookClass                   (:class:`PublishTask`)      : The hook plugin class.
            settings                    (:class:`PluginSetting`)    : The keys are strings, matching the keys returned
                                                                    in the settings property. The values are `Setting`
                                                                    instances.
            item                        (:class:`PublishItem`)      : Item to process
            isChild                     (bool,  optional)           : True if the item is a child, otherwise False.
                                                                    Defaults to False.
        '''
        # Get the node.
        if(isChild):
            node = item.parent.properties["node"]
        else:
            node = item.properties["node"]

        # Get the path to create and publish.
        publish_path = item.properties["path"]

        # Ensure the publish folder exists.
        publish_folder = os.path.dirname(publish_path)
        hookClass.parent.ensure_folder_exists(publish_folder)

        # Execute the run command of the ndoe.
        node.render()

        # Clean the materialX file.
        self.fixMaterialXFile(publish_path)

    # Post publish functions.

    def fixMaterialXFile(self, filePath):
        ''' Fix the materialX file and remove the unwanted material assignations.

        Args:
            filePath    (str)   : The path of the material X.
        '''
        # Clear the content of the mtlx file.
        REGEXDELETE     = r'(.*<materialassign name="materialassign)\d+(" material=".*" geom=")(.*alembic:\d+)(" />\n)'
        REGEXREPLACE    = r'(.*<materialassign name="materialassign)(\d+)(" material=".*" geom=")(.*)(" />\n)'
        # Open the file and read the lines.
        lines = []
        with open(filePath, 'r') as file:
            lines = file.readlines()
        
        # Remove unwanted lines.
        for index in reversed(range(len(lines))):
            line = lines[index]
            if(re.search(REGEXDELETE, line)):
                lines.pop(index)
                
        # Reassign the number of the material assign.
        materialassignIndex = 1        
        for index in range(len(lines)):
            line = lines[index]
            find = re.search(REGEXREPLACE, line)
        
            if(find):
                groups = list(find.groups())
                groups[1] = str(materialassignIndex)
                materialassignIndex += 1
                lines[index] = ''.join(groups)
                
        # Write the lines back to the file.
        with open(filePath, 'w') as file: 
            file.writelines(lines)

    # Reviews.

    def hookUploadReviewValidate(self, hookClass, settings, item):
        ''' Generic implementation of the upload method for a review file validate plugin hook.

        Args:
            hookClass                   (:class:`PublishTask`)      : The hook plugin class.
            settings                    (:class:`PluginSetting`)    : The keys are strings, matching the keys returned
                                                                    in the settings property. The values are `Setting`
                                                                    instances.
            item                        (:class:`PublishItem`)      : Item to process
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
            hookClass                   (:class:`PublishTask`)      : The hook plugin class.
            settings                    (:class:`PluginSetting`)    : The keys are strings, matching the keys returned
                                                                    in the settings property. The values are `Setting`
                                                                    instances.
            item                        (:class:`PublishItem`)      : Item to process
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
            hookClass                   (:class:`PublishTask`)      : The hook plugin class.
            settings                    (:class:`PluginSetting`)    : The keys are strings, matching the keys returned
                                                                    in the settings property. The values are `Setting`
                                                                    instances.
            item                        (:class:`PublishItem`)      : Item to process
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