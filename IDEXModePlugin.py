# Copyright (c) 2023 LifeOfBrian
# This IDEXModePlugin is released under the terms of the AGPLv3 or higher.
# Thanks to Aldo Hoeben / fieldOfView for his great work that made this plugin possible!

from collections import OrderedDict
import json, os

from UM.Extension import Extension
from UM.Application import Application
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Logger import Logger
from typing import Dict, List, Any


class IDEXModePlugin(Extension):
    def __init__(self):
        super().__init__()    
    
        self._application = Application.getInstance()
        
        self._i18n_catalog = None

        self.hello_window = None
        
        settings_definition_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "idex_mode_settings.def.json"
        )
        try:
            with open(settings_definition_path, "r", encoding="utf-8") as f:
                self._settings_dict = json.load(f, object_pairs_hook=OrderedDict)
        except:
            Logger.logException("e", "Could not load IDEX mode settings definition")
            return

        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)

        self._application.getPreferences().addPreference("IDEXModePlugin/settings_made_visible", False)

    def _onContainerLoadComplete(self, container_id: str) -> None:
        if not ContainerRegistry.getInstance().isLoaded(container_id):
            # skip containers that could not be loaded, or subsequent findContainers() will cause an infinite loop
            return

        try:
            container = ContainerRegistry.getInstance().findContainers(id=container_id)[0]
        except IndexError:
            # the container no longer exists
            return

        if not isinstance(container, DefinitionContainer):
            # skip containers that are not definitions
            return
        if container.getMetaDataEntry("type") == "extruder":
            # skip extruder definitions
            return

        try:
            category = container.findDefinitions(key="dual")[0]
        except IndexError:
            Logger.log("e", "Could not find parent category setting to add settings to")
            return

        for setting_key in self._settings_dict.keys():
            setting_definition = SettingDefinition(
                setting_key, container, category, self._i18n_catalog
            )
            setting_definition.deserialize(self._settings_dict[setting_key])

            category._children.append(setting_definition)
            container._definition_cache[setting_key] = setting_definition

            self._expanded_categories = self._application.expandedCategories.copy()
            self._updateAddedChildren(container, setting_definition)
            self._application.setExpandedCategories(self._expanded_categories)
            self._expanded_categories.clear()
            container._updateRelations(setting_definition)

        preferences = self._application.getPreferences()
        if not preferences.getValue("IDEXModePlugin/settings_made_visible"):
            setting_keys = self._getAllSettingKeys(self._settings_dict)

            visible_settings = preferences.getValue("general/visible_settings")
            visible_settings_changed = False
            for key in setting_keys:
                if key not in visible_settings:
                    visible_settings += ";%s" % key
                    visible_settings_changed = True

            if visible_settings_changed:
                preferences.setValue("general/visible_settings", visible_settings)

            preferences.setValue("IDEXModePlugin/settings_made_visible", True)

    def _updateAddedChildren(
        self, container: DefinitionContainer, setting_definition: SettingDefinition
    ) -> None:
        children = setting_definition.children
        if not children or not setting_definition.parent:
            return

        # make sure this setting is expanded so its children show up  in setting views
        if setting_definition.parent.key in self._expanded_categories:
            self._expanded_categories.append(setting_definition.key)

        for child in children:
            container._definition_cache[child.key] = child
            self._updateAddedChildren(container, child)

    def _getAllSettingKeys(self, definition: Dict[str, Any]) -> List[str]:
        children = []
        for key in definition:
            children.append(key)
            if "children" in definition[key]:
                children.extend(self._getAllSettingKeys(definition[key]["children"]))
        return children