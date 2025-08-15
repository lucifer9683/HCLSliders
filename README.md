# HCL Sliders
*HCL Sliders* is a Python plugin made for [Krita](https://krita.org) (free professional and open-source painting program).

This plugin contains sliders for various hue/colorfulness/lightness models for use in the sRGB color space and its linear counterpart. 

### Available Models

**sRGB Color Space**

*HSV* (Hue, Saturation, Value)

*HSL* (Hue, Saturation, Lightness)

*HCY* (Hue, Relative Chroma, Luma/Relative Luminance)

**Oklab Color Space**

*OKHCL* (Hue, Relative Chroma, Referenced Lightness)

*OKHSV* (Hue, Saturation, Value)

*OKHSL* (Hue, Interpolated Saturation, Referenced Lightness)

*OKHCL* (Hue, Chroma, Lightness)

### Accepted CSS Syntax

*Heximal* notations: Must be 6 digits, i.e. `#AABBCC`

*Oklab* notations: RGB values will be clipped to the sRGB gamut, i.e. `oklab(50% 0 0)`

*Oklch* notations: Hue must be given in degrees and RGB will be clipped, i.e. `oklch(50% 0.1 300)`

Some extra non-standard formats are also supported when parsing:

- Heximal without the `#` prefix, i.e. `AABBCC`
- Oklab/Oklch without the `okxxx` and brackets, i.e. `50% 0 0` (Or not using percentage value, like `0.5`)

## Slider Interactions
Left Mouse Button/Pen **Press**: Set value for channel

**Ctrl** + Left Mouse Button/Pen **Press**: Snap value to interval points

**Shift** + Left Mouse Button/Pen **Drag**: Shift value by 0.1 precision

**Alt** + Left Mouse Button/Pen **Drag**: Shift value by 0.01 precision

## History Interactions
Left Mouse Button/Pen **Click**: Set color to foreground

**Ctrl** + Left Mouse Button/Pen **Click**: Set color to background

**Shift** + Left Mouse Button/Pen **Drag**: Scroll color history

**Alt** + Left Mouse Button/Pen **Click**: Delete selected color from history

**Alt** + Left Mouse Button/Pen **Drag**: Delete a series of colors from history, starting from the point where mouse/pen is pressed until where the mouse/pen is released

## (New) Background Selector Mode
**Click** on the color display panel on the plugin to toggle between selecting foreground and background color.

## Install/Update
1. Download the [ZIP file](https://github.com/lucifer9683/HCLSliders/releases/download/v1.1.5/HCLSlidersV1.1.5.zip)
2. Open Krita and go to Tools -> Scripts -> Import Python Plugin From File.
3. Navigate to the download location and select the ZIP file.
4. Restart Krita.
5. Go to the Python Plugin Manager again to check if Ten Brush Slots extension is activated.
6. If not activated, click on the checkbox beside it and restart Krita again.
7. Go to Settings -> Dockers -> HCL Sliders, click on the checkbox to activate it.
