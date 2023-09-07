# Cura-IDEX-mode-plugin
This tiny plugin adds a custom parameter called **IDEX Mode** to the Cura sidebar under the Dual Extrusion category that is passed to the slicer start code/gcode and can be processed later via Klipper macros.

![cura_mod_gh_new](https://github.com/Life0fBrian/Cura-IDEX-mode-plugin/assets/84620081/3ebc3600-f840-4f9b-a0e0-442c2272e4b1)
![cura_mod_gh_new2](https://github.com/Life0fBrian/Cura-IDEX-mode-plugin/assets/84620081/0e207f37-1065-44cf-8d75-51f4ccbc3044)


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

There is now an enhancement for users of printer/platform models:
![printer_model](https://github.com/Life0fBrian/Cura-IDEX-mode-plugin/assets/84620081/80a93d51-fcde-478e-b07e-37145dc77f86)
When you now have the option **Adapt bed width** selected and choose **mirror** or **copy** mode the platform model moves respectively so that the changed print area properly fits to the underlying bed/platform model.

## To-Dos:
- ~~Halve the width of the build plate when IDEX mode `copy` or `mirror` is selected to get a better feeling for the maximum possible object size.~~
- ~~Disabling/hiding IDEX menu items when on single extruder printer.~~ -> Setting fixed to IDEX.
- Adapting position of a printer platform model to used IDEX mode -> still WIP; when on copy or mirror mode during first load of Cura or printer switching the option "Adapt bed width" needs to be toggled once to get it synced again.

## Changelog:
- 2023-08-09: Creation of this project
- 2023-08-15: Updated plugin to v0.0.2 - depending on IDEX mode the second extruder becomes disabled - adaption of build plate width still in progress.
- 2023-08-17: Updated plugin to v0.1.0 - optimized code and added adaption of built plate width depending on selected IDEX mode.
- 2023-08-22: Updated plugin to v0.2.0 - added parameter to enable or disable adaption of bed width. Fixed bug causing Cura to crash when switching to single extruder printer.
- 2023-08-23: Updated plugin to v0.2.5 - when on single extruder printer IDEX mode is set to IDEX only. Added additional photo on top of this page.
- 2023-09-07: Updated plugin to v0.5.5 - when a printer platform model is present/loaded its position will be adapted to the IDEX mode as well.
