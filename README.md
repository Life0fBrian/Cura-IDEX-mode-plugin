# Cura-IDEX-mode-plugin
This tiny plugin adds a custom parameter called **IDEX Mode** to the Cura sidebar under the Dual Extrusion category that is passed to the slicer start code/gcode and can be processed later via Klipper macros.

![cura_mod_gh_new](https://github.com/Life0fBrian/Cura-IDEX-mode-plugin/assets/84620081/3ebc3600-f840-4f9b-a0e0-442c2272e4b1)

The need for this plugin came up due to my IDEX printer mod and the IDEX Klipper branch of [@dmbutyugin](https://github.com/dmbutyugin):
https://github.com/dmbutyugin/klipper/tree/idex

This branch makes it possible for Klipper to support all IDEX modes: **IDEX**, **copy** and **mirror**.

However until now you need to set up the respective mode in the Klipper macros before slicing the models.
This plugin now lets you select the IDEX mode already in Cura and the parameter can be accessed via the variable `{idex_mode}` in the slicer start code:

`PRINT_START BED_TEMP={material_bed_temperature_layer_0} HOTEND_TEMP0={material_print_temperature_layer_0, 0} HOTEND_TEMP1={material_print_temperature_layer_0, 1} IDEX_MODE={idex_mode}`
(This example also shows how to get the initial layer temps of both extruders)
This could look in the resulting gcode like follows:

`PRINT_START BED_TEMP=65 HOTEND_TEMP0=210.0 HOTEND_TEMP1=205.0 IDEX_MODE=idex`

Then you can process this parameter inside your Klipper `PRINT_START` macro for example with the following code:
```
    {% set idex_mode = params.IDEX_MODE|default("idex")|string %}

    {% if idex_mode == "idex"%}
      # initialize idex mode
    {% elif idex_mode == "copy" %}
      # initialize copy mode
    {% elif idex_mode == "mirror" %}
      # initialize mirror mode
    {% endif %}
```

## To-Dos:
- Halve the width of the build plate when IDEX mode `copy` or `mirror` is selected to get a better feeling for the maximum possible object size.

## Changelog:
- 2023-08-09: Creation of this project
- 2023-08-15: Updated plugin to v0.0.2 - depending on IDEX mode the second extruder becomes disabled - adaption of build plate width still in progress.
- 2023-08-17: Updated plugin to v0.1.0 - optimized code and added adaption of built plate width depending on selected IDEX mode.
- 2023-08-22: Updated plugin to v0.2.0 - added parameter to enable or disable adaption of bed width. Fixed bug causing Cura to crash when switching to single extruder printer.
