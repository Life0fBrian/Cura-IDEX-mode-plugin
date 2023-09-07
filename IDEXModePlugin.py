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
from copy import deepcopy

from UM.Scene.Platform import Platform
from UM.Scene.SceneNode import SceneNode
from UM.Math.Vector import Vector
from cura.CuraApplication import CuraApplication
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator

from UM.Message import Message


class IDEXModePlugin(Extension):
    
    def __init__(self):
        super().__init__()    
    
        self._application = Application.getInstance()
                
        self._i18n_catalog = None
        self._build_width = 0   #build plate width initilization
        self._platform_offset = [0, 0, 0]
        self._platform_new_offset = [0, 0, 0]
        self._root_node = None
        
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
        
    #get the printers bed width (x axis) from the definitions
    def _getXWidth(self):
        machine_manager = self._application.getMachineManager()
        global_stack = machine_manager.activeMachine
        definition_changes = global_stack.definitionChanges
            #add check whether definitions contain a value; if not read it from global stack   
        if definition_changes.getProperty("machine_width", "value") != None:
            x_width = definition_changes.getProperty("machine_width", "value")
        else:   #use default from global stack
            x_width = self._global_container_stack.getProperty("machine_width", "default_value")
            
        return x_width

    #if a custom build plate model (STL or 3MF) is present get its offset
    def _getPlatformOffset(self):
        platform_offset = [0,0,0] #initialize variable
        self._global_container_stack = Application.getInstance().getGlobalContainerStack()
        if self._global_container_stack:
            container = self._global_container_stack.findContainer({ "platform": "*" })
            if container:
                platform_offset = container.getMetaDataEntry("platform_offset")
                if not platform_offset:
                    platform_offset = [0,0,0]

            return platform_offset
        else:
            return None

    def _addPlatformXOffset(self):
        offset = deepcopy(self._platform_offset)
        x_offset = offset[0]
       
        offset[0] = float(x_offset) + float(self._build_width / 4)
    
        return offset

    def _onContainerLoadComplete(self, container_id: str) -> None:
        if not ContainerRegistry.getInstance().isLoaded(container_id):
            #skip containers that could not be loaded, or subsequent findContainers() will cause an infinite loop
            return

        try:
            container = ContainerRegistry.getInstance().findContainers(id=container_id)[0]
        except IndexError:
            #container does not exist
            return

        if not isinstance(container, DefinitionContainer):
            #skip containers that are not definitions
            return
        if container.getMetaDataEntry("type") == "extruder":
            #skip extruder definitions
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
            self._build_width = self._getXWidth()
            self._platform_offset = self._getPlatformOffset()
            self._platform_new_offset = self._addPlatformXOffset()

            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)
            
            #calling _onPropertyChanged for initialization
            self._onPropertyChanged("machine_width", "value")
            self._onPropertyChanged("idex_mode", "value")

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        extruder_count = len(self._global_container_stack.extruderList)
        
        if extruder_count > 1:
            self._root_node = CuraApplication.getInstance().getController().getScene().getRoot()
            idex_mode = self._global_container_stack.getProperty("idex_mode", "value")
            adapt_width = self._global_container_stack.getProperty("idex_change_width", "value")
            
            offset = self._platform_offset
            offset_adapt = self._platform_new_offset

            if key == "idex_change_width" and property_name == "value":
                if adapt_width:
                    self._global_container_stack.setProperty("machine_width", "value", self._build_width / 2)
                else:
                    self._global_container_stack.setProperty("machine_width", "value", self._build_width)
        
            elif key == "machine_width" and property_name == "value":
                self._build_width = self._getXWidth()
                self._platform_offset = self._getPlatformOffset()
                self._platform_new_offset = self._addPlatformXOffset()
                self._onPropertyChanged("idex_mode", "value")
                                
            elif key == "idex_mode" and property_name == "value":
                extruder_t0 = self._global_container_stack.extruderList[0]
                extruder_t1 = self._global_container_stack.extruderList[1]
                                
                if idex_mode in ["mirror", "copy"]:
                    self._application.getMachineManager().setExtruderEnabled(0, True)
                    self._application.getMachineManager().setExtruderEnabled(1, False)
                    
                    if adapt_width:
                        self._global_container_stack.setProperty("machine_width", "value", self._build_width / 2)
                        for node in BreadthFirstIterator(self._root_node):
                            #message = Message("", title = "")
                            #message.show()

                            if isinstance(node, Platform):
                                node.setPosition(Vector(offset_adapt[0], offset_adapt[1], offset_adapt[2], 3))
                    else:
                        self._global_container_stack.setProperty("machine_width", "value", self._build_width)
  
                        for node in BreadthFirstIterator(self._root_node):
                            if isinstance(node, Platform):
                                node.setPosition(Vector(offset[0], offset[1], offset[2]))      

                elif idex_mode == "idex":
                    self._application.getMachineManager().setExtruderEnabled(0, True)
                    self._application.getMachineManager().setExtruderEnabled(1, True)
                    self._global_container_stack.setProperty("machine_width", "value", self._build_width)
                    for node in BreadthFirstIterator(self._root_node):
                        if isinstance(node, Platform):
                            node.setPosition(Vector(offset[0], offset[1], offset[2]))
                            
                extruder_t0.enabledChanged.connect(self._onEnabledChangedT0)
                extruder_t1.enabledChanged.connect(self._onEnabledChangedT1)
                
        else:   #for single extruder printers set IDEX mode to always idex
            if key == "idex_mode" and property_name == "value":
                self._global_container_stack.setProperty("idex_mode", "value", "idex")

    def _onEnabledChangedT0(self):
        idex_mode = self._global_container_stack.getProperty("idex_mode", "value")
        #to-do: change available idex modes depending on available extruders

    def _onEnabledChangedT1(self):
        idex_mode = self._global_container_stack.getProperty("idex_mode", "value")
        #to-do: change available idex modes depending on available extruders
