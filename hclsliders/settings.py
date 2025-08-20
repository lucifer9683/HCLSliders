DOCKER_NAME = 'HCL Sliders'
# adjust plugin sizes and update timing here
TIME = 100 # ms time for plugin to update color from krita, faster updates may make krita slower
DELAY = 300 # ms delay updating color history to prevent flooding when using the color picker
DISPLAY_HEIGHT = 25 # px for color display panel at the top
CHANNEL_HEIGHT = 19 # px for channels, also influences hex/ok syntax box and buttons
MODEL_SPACING = 6 # px for spacing between color models
HISTORY_HEIGHT = 16 # px for color history and area of each color box
VALUES_WIDTH = 63 # px for spinboxes containing channel values
LABEL_WIDTH = 11 # px for spacing of channel indicator/letter
# adjust various sizes of config menu
CONFIG_SIZE = (468, 230) # (width in px, height in px) size for config window
SIDEBAR_WIDTH = 76 # px for sidebar containing channel selection and others button 
GROUPBOX_HEIGHT = 64 # px for groupboxes of cursor snapping, chroma mode and color history
SPINBOX_WIDTH = 72 # px for spinboxes of interval, displacement and memory
OTHERS_HEIGHT = 12 # px for spacing before color history in others page
# compatible color profiles in krita
SRGB = ('sRGB-elle-V2-srgbtrc.icc', 'sRGB built-in', 
        'Gray-D50-elle-V2-srgbtrc.icc', 'Gray-D50-elle-V4-srgbtrc.icc')
LINEAR = ('sRGB-elle-V2-g10.icc', 'krita-2.5, lcms sRGB built-in with linear gamma TRC', 
          'Gray-D50-elle-V2-g10.icc', 'Gray-D50-elle-V4-g10.icc')
NOTATION = ('HEX', 'OKLAB', 'OKLCH')
