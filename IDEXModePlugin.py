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
from cura import CuraActions
from typing import Dict, List, Any


class IDEXModePlugin(Extension):
    
    def __init__(self):
        super().__init__()    
    
        self._application = Application.getInstance()
        self._curaActions = CuraActions.CuraActions()
                
        self._i18n_catalog = None
        
        settings_definition_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "idex_mode_settings.def.json")
        try:
            with open(settings_definition_path, "r", encoding="utf-8") as f:
                self._settings_dict = json.load(f, object_pairs_hook=OrderedDict)
        except:
            Logger.logException("e", "Could not load IDEX mode settings definition")
            return

        self._global_container_stack = self._application.getGlobalContainerStack()

        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged()        
        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)

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
            setting_definition = SettingDefinition(setting_key, container, category, self._i18n_catalog)
            setting_definition.deserialize(self._settings_dict[setting_key])

            category._children.append(setting_definition)
            container._definition_cache[setting_key] = setting_definition

            self._expanded_categories = self._application.expandedCategories.copy()
            self._updateAddedChildren(container, setting_definition)
            self._application.setExpandedCategories(self._expanded_categories)
            self._expanded_categories.clear()
            container._updateRelations(setting_definition)

    def _updateAddedChildren(self, container: DefinitionContainer, setting_definition: SettingDefinition) -> None:
        children = setting_definition.children
        if not children or not setting_definition.parent:
            return

        # make sure this setting is expanded so its children show up in setting views
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

    def _onGlobalContainerStackChanged(self):
        self._global_container_stack = self._application.getGlobalContainerStack()
        if self._global_container_stack:
            global_stack = self._application.getMachineManager().activeMachine
                
            if not global_stack:
                return

            definition = global_stack.getDefinition()
                
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)
            
            # Calling _onPropertyChanged as an initialization
            self._onPropertyChanged("idex_mode", "value")

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if key == "idex_mode" and property_name == "value":
            idex_mode = self._global_container_stack.getProperty("idex_mode", "value")
            extruder_t0 = self._global_container_stack.extruderList[0]
            extruder_t1 = self._global_container_stack.extruderList[1]

            if idex_mode == "mirror" or idex_mode == "copy":
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, False)

            elif idex_mode == "idex":
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, True)