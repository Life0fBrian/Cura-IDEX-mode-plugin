# Cura-IDEX-mode-plugin
This tiny plugin adds a custom parameter called **IDEX Mode** to the Cura sidebar under the Dual Extrusion category that is passed to the slicer start code/gcode and can be processed later via Klipper macros.

![cura_mod](https://github.com/Life0fBrian/Cura-IDEX-mode-plugin/assets/84620081/b59db85a-f8ba-432b-91bc-99fa75a1ceb6)

The need for this plugin came up due to my IDEX printer mod and the IDEX Klipper branch of [@dmbutyugin](https://github.com/dmbutyugin):
https://github.com/dmbutyugin/klipper/tree/idex

This branch makes it possible for Klipper to support all IDEX modes: IDEX, copy and mirror.

However until now you need to set up the respective mode in the Klipper macros before slicing the models.
This plugin now lets you select the IDEX mode already in Cura and the parameter can be accessed via the variable **{idex_mode}** in the slicer start code:
>PRINT_START BED_TEMP={material_bed_temperature_layer_0} HOTEND_TEMP={material_print_temperature_layer_0} IDEX_MODE={idex_mode}

This could look in the resulting gcode like follows: 
>PRINT_START BED_TEMP=65 HOTEND_TEMP=210.0 IDEX_MODE=idex
