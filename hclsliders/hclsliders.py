# SPDX-License-Identifier: GPL-3.0-or-later
#
# HCL Sliders is a Krita plugin for color selection.
# Copyright (C) 2024  Lucifer <krita-artists.org/u/Lucifer>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This file incorporates work covered by the following copyright and  
# permission notice:
#
#   Pigment.O is a Krita plugin and it is a Color Picker and Color Mixer.
#   Copyright ( C ) 2020  Ricardo Jeremias.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   ( at your option ) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QPainter, QBrush, QColor, QLinearGradient, QPixmap, QIcon
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QDoubleSpinBox, QLabel, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QDialog, QStackedWidget, 
                             QTabWidget, QCheckBox, QGroupBox, QRadioButton, QSpinBox)
from krita import DockWidget, ManagedColor

from .colorconversion import Convert

DOCKER_NAME = 'HCL Sliders'
TIME = 100 # ms time for plugin to update color from krita, faster updates may make krita slower
DELAY = 300 # ms delay updating color history to prevent flooding when using the color picker
DISPLAY_HEIGHT = 25 # px for color display panel at the top
CHANNEL_HEIGHT = 19 # px for channels, also influences hex/ok syntax box and buttons
HISTORY_HEIGHT = 16 # px for color history and area of each color box
# compatible color profiles in krita
SRGB = ('sRGB-elle-V2-srgbtrc.icc', 'sRGB built-in')
LINEAR = ('sRGB-elle-V2-g10.icc', 'krita-2.5, lcms sRGB built-in with linear gamma TRC')
NOTATION = ('HEX', 'OKLAB', 'OKLCH')


class ColorDisplay(QWidget):
    
    def __init__(self, parent):
        super().__init__(parent)

        self.hcl = parent
        self.current = None
        self.recent = None
        self.foreground = None
        self.background = None

    def setCurrentColor(self, color=None):
        self.current = color
        self.update()

    def setForeGroundColor(self, color=None):
        self.foreground = color
        self.update()

    def setBackGroundColor(self, color=None):
        self.background = color
        self.update()

    def resetColors(self):
        self.current = None
        self.recent = None
        self.foreground = None
        self.background = None
        self.update()

    def isChanged(self):
        if self.current is None:
            return True
        if self.current.components() != self.foreground.components():
            return True
        if self.current.colorModel() != self.foreground.colorModel():
            return True
        if self.current.colorDepth() != self.foreground.colorDepth():
            return True
        if self.current.colorProfile() != self.foreground.colorProfile():
            return True
        return False
    
    def isChanging(self):
        if self.recent is None:
            return False
        if self.recent.components() != self.current.components():
            return True
        if self.recent.colorModel() != self.current.colorModel():
            return True
        if self.recent.colorDepth() != self.current.colorDepth():
            return True
        if self.recent.colorProfile() != self.current.colorProfile():
            return True
        return False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        width = self.width()
        halfwidth = round(width / 2.0)
        height = self.height()
        # foreground color from krita
        if self.foreground:
            painter.setBrush(QBrush(self.foreground.colorForCanvas(self.hcl.canvas())))
        else:
            painter.setBrush( QBrush(QColor(0, 0, 0)))
        painter.drawRect(0, 0, width, height)
        # current color from sliders
        if self.current:
            painter.setBrush(QBrush(self.current.colorForCanvas(self.hcl.canvas())))
            painter.drawRect(0, 0, halfwidth, height)
        if self.background:
            painter.setBrush(QBrush(self.background.colorForCanvas(self.hcl.canvas())))
            painter.drawRect(halfwidth, 0, width - halfwidth, height)


class ColorHistory(QListWidget):

    def __init__(self, hcl, parent=None):
        super().__init__(parent)
        # should not pass in hcl as parent if it can be hidden
        self.hcl = hcl
        self.index = -1
        self.modifier = None
        self.start = 0
        self.position = 0
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setFixedHeight(HISTORY_HEIGHT)
        self.setViewportMargins(-2, 0, 0, 0)
        # grid width + 2 to make gaps between swatches
        self.setGridSize(QSize(HISTORY_HEIGHT + 2, HISTORY_HEIGHT))
        self.setUniformItemSizes(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QListWidget.SelectionMode.NoSelection)

    def startScrollShift(self, event):
        self.start = self.horizontalScrollBar().value()
        self.position = event.x()
    
    def keyPressEvent(self, event):
        # disable keyboard interactions
        pass

    def mousePressEvent(self, event):
        self.hcl.setPressed(True)
        item = self.itemAt(event.pos())
        index = self.row(item)

        if index != -1:
            if (event.buttons() == Qt.MouseButton.LeftButton and 
                event.modifiers() == Qt.KeyboardModifier.NoModifier):
                color = self.hcl.makeManagedColor(*self.hcl.pastColors[index])
                self.hcl.color.setCurrentColor(color)
                self.index = index
                self.modifier = Qt.KeyboardModifier.NoModifier
            elif (event.buttons() == Qt.MouseButton.LeftButton and 
                event.modifiers() == Qt.KeyboardModifier.ControlModifier):
                color = self.hcl.makeManagedColor(*self.hcl.pastColors[index])
                self.hcl.color.setBackGroundColor(color)
                self.index = index
                self.modifier = Qt.KeyboardModifier.ControlModifier
            elif (event.buttons() == Qt.MouseButton.LeftButton and 
                event.modifiers() == Qt.KeyboardModifier.AltModifier):
                self.index = index
                self.modifier = Qt.KeyboardModifier.AltModifier
        self.startScrollShift(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            event.modifiers() == Qt.KeyboardModifier.ShiftModifier):
            position = 0
            bar = self.horizontalScrollBar()
            if bar.maximum():
                # speed of grid width squared seems good
                speed = (HISTORY_HEIGHT + 2) ** 2
                # move bar at constant speed
                shift = float(self.position - event.x()) / self.width()
                position = round(self.start + shift * speed)
            bar.setValue(position)
        else:
            self.startScrollShift(event)

    def mouseReleaseEvent(self, event):
        item = self.itemAt(event.pos())
        index = self.row(item)

        if index == self.index and index != -1:
            if (event.modifiers() == Qt.KeyboardModifier.NoModifier and 
                self.modifier == Qt.KeyboardModifier.NoModifier):
                self.hcl.setPastColorToFG(index)
            elif (event.modifiers() == Qt.KeyboardModifier.ControlModifier and 
                  self.modifier == Qt.KeyboardModifier.ControlModifier):
                self.hcl.setPastColorToBG()
        
        if (event.modifiers() == Qt.KeyboardModifier.AltModifier and 
            self.modifier == Qt.KeyboardModifier.AltModifier):
            if self.index != -1 and index != -1 :
                start = index
                stop = self.index
                if self.index > index:
                    start = self.index
                    stop = index
                for i in range(start, stop - 1, -1):
                    self.takeItem(i)
                    self.hcl.pastColors.pop(i)

        if self.modifier == Qt.KeyboardModifier.NoModifier:
            # prevent setHistory when krita fg color not changed
            self.hcl.color.current = self.hcl.color.foreground
        elif self.modifier == Qt.KeyboardModifier.ControlModifier:
            self.hcl.color.setBackGroundColor()
        
        self.modifier = None
        self.index = -1
        self.hcl.setPressed(False)


class ChannelSlider(QWidget):

    valueChanged = pyqtSignal(float)
    mousePressed = pyqtSignal(bool)

    def __init__(self, limit: float, parent=None):
        super().__init__(parent)

        self.value = 0.0
        self.limit = limit
        self.interval = 0.1
        self.displacement = 0
        self.start = 0.0
        self.position = 0
        self.shift = 0.1
        self.colors = []

    def setGradientColors(self, colors: list):
        if self.colors:
            self.colors = []
        for rgb in colors:
            # using rgbF as is may result in black as colors are out of gamut
            color = QColor(*rgb)
            self.colors.append(color)
        self.update()

    def setValue(self, value: float):
        self.value = value
        self.update()

    def setLimit(self, value: float):
        self.limit = value
        self.update()

    def setInterval(self, interval: float):
        limit = 100.0 if self.limit < 360 else 360.0
        if interval < 0.1:
            interval = 0.1
        elif interval > limit:
            interval = limit
        self.interval = interval

    def setDisplacement(self, displacement: float):
        limit = 99.9 if self.limit < 360 else 359.9
        if displacement < 0:
            displacement = 0
        elif displacement > limit:
            displacement = limit
        self.displacement = displacement

    def emitValueChanged(self, event):
        position = event.x()
        width = self.width()
        if position > width:
            position = width
        elif position < 0:
            position = 0.0
        self.value = round((position / width) * self.limit, 3)
        self.valueChanged.emit(self.value)
        self.mousePressed.emit(True)

    def emitValueSnapped(self, event):
        position = event.x()
        width = self.width()
        if position > width:
            position = width
        elif position < 0:
            position = 0.0
        value = round((position / width) * self.limit, 3)

        if value != 0 and value != self.limit:
            interval = self.interval if self.interval != 0 else self.limit
            if self.limit < 100:
                interval = (self.interval / 100) * self.limit
            displacement = (value - self.displacement) % interval
            if displacement < interval / 2:
                value -= displacement
            else:
                value += interval - displacement
            if value > self.limit:
                value = self.limit
            elif value < 0:
                value = 0.0
        
        self.value = value
        self.valueChanged.emit(self.value)
        self.mousePressed.emit(True)
    
    def startValueShift(self, event):
        self.start = self.value
        self.position = event.x()
    
    def emitValueShifted(self, event):
        position = event.x()
        vector = position - self.position
        value = self.start + (vector * self.shift)

        if value < 0:
            if self.limit == 360:
                value += self.limit
            else:
                value = 0
        elif value > self.limit:
            if self.limit == 360:
                value -= self.limit
            else:
                value = self.limit
          
        self.value = value
        self.valueChanged.emit(self.value)
        self.mousePressed.emit(True)

    def mousePressEvent(self, event):
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            event.modifiers() == Qt.KeyboardModifier.NoModifier):
            self.emitValueChanged(event)
        elif (event.buttons() == Qt.MouseButton.LeftButton and 
              event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            self.emitValueSnapped(event)
        self.startValueShift(event)
        self.update()

    def mouseMoveEvent(self, event):
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            event.modifiers() == Qt.KeyboardModifier.NoModifier):
            self.emitValueChanged(event)
            self.startValueShift(event)
        elif (event.buttons() == Qt.MouseButton.LeftButton and 
              event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            self.emitValueSnapped(event)
            self.startValueShift(event)
        elif (event.buttons() == Qt.MouseButton.LeftButton and 
              event.modifiers() == Qt.KeyboardModifier.ShiftModifier):
            self.shift = 0.1
            self.emitValueShifted(event)
        elif (event.buttons() == Qt.MouseButton.LeftButton and 
              event.modifiers() == Qt.KeyboardModifier.AltModifier):
            self.shift = 0.01
            self.emitValueShifted(event)
        self.update()

    def mouseReleaseEvent(self, event):
        self.mousePressed.emit(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        # background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush( QBrush(QColor(0, 0, 0, 50)))
        painter.drawRect(0, 1, width, height - 2)
        # gradient
        gradient = QLinearGradient(0, 0, width, 0)
        if self.colors:
            for index, color in enumerate(self.colors):
                gradient.setColorAt(index / (len(self.colors) - 1), color)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(1, 2, width - 2, height - 4)
        # cursor
        if self.limit:
            position = round((self.value / self.limit) * (width - 2))
            painter.setBrush( QBrush(QColor(0, 0, 0, 100)))
            painter.drawRect(position - 2, 0, 6, height)
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.drawRect(position, 1, 2, height - 2)


class ColorChannel:

    channelList = None

    def __init__(self, name: str, parent):
        self.name = name
        self.update = parent.updateChannels
        self.refresh = parent.updateChannelGradients
        wrap = False
        interval = 10.0
        displacement = 0.0
        self.scale = True
        self.clip = 0.0
        self.colorful = False
        self.luma = False
        self.limit = 100.0
        if self.name[-3:] == "Hue":
            wrap = True
            interval = 30.0
            if self.name[:2] == "ok":
                interval = 40.0
                displacement = 25.0
            self.limit = 360.0
        elif self.name[-6:] == "Chroma":
            self.limit = 0.0
        self.layout = QHBoxLayout()
        self.layout.setSpacing(2)

        if self.name[:2] == "ok":
            tip = f"{self.name[:5].upper()} {self.name[5:]}"
            letter = self.name[5:6]
        else:
            tip = f"{self.name[:3].upper()} {self.name[3:]}"
            if self.name[-4:] == "Luma":
                letter = "Y"
            else:
                letter = self.name[3:4]
        self.label = QLabel(letter)
        self.label.setFixedHeight(CHANNEL_HEIGHT - 1)
        self.label.setFixedWidth(11)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setToolTip(tip)

        self.slider = ChannelSlider(self.limit)
        self.slider.setFixedHeight(CHANNEL_HEIGHT)
        self.slider.setMinimumWidth(100)
        self.slider.setInterval(interval)
        self.slider.setDisplacement(displacement)
        self.slider.mousePressed.connect(parent.setPressed)

        self.spinBox = QDoubleSpinBox()
        if self.name[-6:] == "Chroma":
            self.spinBox.setDecimals(3)
        self.spinBox.setMaximum(self.limit)
        self.spinBox.setWrapping(wrap)
        self.spinBox.setFixedHeight(CHANNEL_HEIGHT)
        self.spinBox.setFixedWidth(63)
        self.spinBox.editingFinished.connect(parent.finishEditing)

        self.slider.valueChanged.connect(self.updateSpinBox)
        self.spinBox.valueChanged.connect(self.updateSlider)
        ColorChannel.updateList(name)

    def value(self):
        return self.spinBox.value()
    
    def setValue(self, value: float):
        if self.name[-6:] == "Chroma" and self.limit >= 10:
            value = round(value, 2)
        self.slider.setValue(value)
        self.spinBox.setValue(value)

    def setLimit(self, value: float):
        decimal = 2 if value >= 10 else 3
        self.limit = round(value, decimal)
        self.slider.setLimit(self.limit)
        self.spinBox.setDecimals(decimal)
        self.spinBox.setMaximum(self.limit)
        self.spinBox.setSingleStep(self.limit / 100)

    def clipChroma(self, clip: bool):
        # do not set chroma channel itself to clip as the clip value will not be updated when adjusting
        self.scale = not clip
        self.refresh()

    def colorfulHue(self, colorful: bool):
        self.colorful = colorful
        self.refresh()

    def updateSlider(self, value: float):
        self.update(value, self.name, "slider")

    def updateSpinBox(self, value: float):
        self.update(value, self.name, "spinBox")
    
    def updateGradientColors(self, firstConst: float, lastConst: float, trc: str, ChromaLimit: float=-1):
        colors = []
        if self.name[-3:] == "Hue":
            if self.name[:2] == "ok":
                # oklab hue needs more points for qcolor to blend more accurately
                # range of 0 to 25 - 345 in 15deg increments to 360
                points = 26
                increment = self.limit / (points - 2)
                displacement = increment - 25

                if self.colorful:
                    for number in range(points):
                        hue = (number - 1) * increment - displacement
                        if hue < 0:
                            hue = 0
                        elif hue > self.limit:
                            hue = self.limit
                        rgb = Convert.okhsvToRgbF(hue, 100.0, 100.0, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[:5] == "okhcl":
                    for number in range(points):
                        hue = (number - 1) * increment - displacement
                        if hue < 0:
                            hue = 0
                        elif hue > self.limit:
                            hue = self.limit
                        rgb = Convert.okhclToRgbF(hue, firstConst, lastConst, ChromaLimit, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[:5] == "okhsv":
                    for number in range(points):
                        hue = (number - 1) * increment - displacement
                        if hue < 0:
                            hue = 0
                        elif hue > self.limit:
                            hue = self.limit
                        rgb = Convert.okhsvToRgbF(hue, firstConst, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[:5] == "okhsl":
                    for number in range(points):
                        hue = (number - 1) * increment - displacement
                        if hue < 0:
                            hue = 0
                        elif hue > self.limit:
                            hue = self.limit
                        rgb = Convert.okhslToRgbF(hue, firstConst, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
            else:
                # range of 0 to 360deg incrementing by 30deg
                points = 13
                increment = self.limit / (points - 1)

                if self.colorful:
                    if self.name[:3] != "hcy":
                        for number in range(points):
                            rgb = Convert.hsvToRgbF(number * increment, 100.0, 100.0, trc)
                            colors.append(Convert.rgbFToInt8(*rgb, trc))
                    else:
                        for number in range(points):
                            rgb = Convert.hcyToRgbF(number * increment, 100.0, -1, -1, trc, self.luma)
                            colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[:3] == "hsv":
                    for number in range(points):
                        rgb = Convert.hsvToRgbF(number * increment, firstConst, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[:3] == "hsl":
                    for number in range(points):
                        rgb = Convert.hslToRgbF(number * increment, firstConst, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[:3] == "hcy":
                    for number in range(points):
                        rgb = Convert.hcyToRgbF(number * increment, firstConst, lastConst, 
                                                ChromaLimit, trc, self.luma)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
        else:
            # range of 0 to 100% incrementing by 10%
            points = 11
            increment = self.limit / (points - 1)

            if self.name[:3] == "hsv":
                if self.name[3:] == "Saturation":
                    for number in range(points):
                        rgb = Convert.hsvToRgbF(firstConst, number * increment, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[3:] == "Value":
                    for number in range(points):
                        rgb = Convert.hsvToRgbF(firstConst, lastConst, number * increment, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
            elif self.name[:3] == "hsl":
                if self.name[3:] == "Saturation":
                    for number in range(points):
                        rgb = Convert.hslToRgbF(firstConst, number * increment, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[3:] == "Lightness":
                    for number in range(points):
                        rgb = Convert.hslToRgbF(firstConst, lastConst, number * increment, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
            elif self.name[:3] == "hcy":
                if self.name[3:] == "Chroma":
                    for number in range(points):
                        rgb = Convert.hcyToRgbF(firstConst, number * increment, lastConst, 
                                                ChromaLimit, trc, self.luma)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[3:] == "Luma":
                    for number in range(points):
                        rgb = Convert.hcyToRgbF(firstConst, lastConst, number * increment, 
                                                ChromaLimit, trc, self.luma)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
            elif self.name[:5] == "okhcl":
                if self.name[5:] == "Chroma":
                    for number in range(points):
                        rgb = Convert.okhclToRgbF(firstConst, number * increment, lastConst, 
                                                  ChromaLimit, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[5:] == "Lightness":
                    for number in range(points):
                        rgb = Convert.okhclToRgbF(firstConst, lastConst, number * increment, 
                                                  ChromaLimit, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
            elif self.name[:5] == "okhsv":
                if self.name[5:] == "Saturation":
                    for number in range(points):
                        rgb = Convert.okhsvToRgbF(firstConst, number * increment, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[5:] == "Value":
                    for number in range(points):
                        rgb = Convert.okhsvToRgbF(firstConst, lastConst, number * increment, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
            elif self.name[:5] == "okhsl":
                if self.name[5:] == "Saturation":
                    for number in range(points):
                        rgb = Convert.okhslToRgbF(firstConst, number * increment, lastConst, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))
                elif self.name[5:] == "Lightness":
                    for number in range(points):
                        rgb = Convert.okhslToRgbF(firstConst, lastConst, number * increment, trc)
                        colors.append(Convert.rgbFToInt8(*rgb, trc))

        self.slider.setGradientColors(colors)

    def blockSignals(self, block: bool):
        self.slider.blockSignals(block)
        self.spinBox.blockSignals(block)

    @classmethod
    def updateList(cls, name: str):
        if cls.channelList is None:
            cls.channelList = []
        cls.channelList.append(name)

    @classmethod
    def getList(cls):
        return cls.channelList.copy()
        

class SliderConfig(QDialog):
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.hcl = parent
        self.setWindowTitle("Configure HCL Sliders")
        self.setFixedSize(468, 230)
        self.mainLayout = QHBoxLayout(self)
        self.loadPages()

    def loadPages(self):
        self.pageList = QListWidget()
        self.pageList.setFixedWidth(76)
        self.pageList.setDragEnabled(True)
        self.pageList.viewport().setAcceptDrops(True)
        self.pageList.setDropIndicatorShown(True)
        self.pageList.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.pages = QStackedWidget()

        hidden = ColorChannel.getList()
        self.models = {}
        for name in self.hcl.displayOrder:
            if name[:2] == "ok":
                self.models.setdefault(name[:5].upper(), []).append(name)
            else:
                self.models.setdefault(name[:3].upper(), []).append(name)
            hidden.remove(name)
        visible = list(self.models.keys())
        for name in hidden:
            if name[:2] == "ok":
                self.models.setdefault(name[:5].upper(), []).append(name)
            else:
                self.models.setdefault(name[:3].upper(), []).append(name)
        
        self.checkBoxes = {}
        for model, channels in self.models.items():
            tabs = QTabWidget()
            tabs.setMovable(True)
            
            for name in channels:
                tab = QWidget()
                tabLayout = QVBoxLayout()
                tabLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
                tab.setLayout(tabLayout)
                channel: ColorChannel = getattr(self.hcl, name)

                snapGroup = QGroupBox("Cursor Snapping")
                snapGroup.setFixedHeight(64)
                snapGroup.setToolTip("Ctrl + Click to snap cursor at intervals")
                snapLayout = QHBoxLayout()
                interval = QDoubleSpinBox()
                interval.setFixedWidth(72)
                interval.setDecimals(1)
                interval.setMinimum(0.1)
                snapLayout.addWidget(interval)
                intervalLabel = QLabel("Interval")
                intervalLabel.setToolTip("Sets the snap interval to amount")
                snapLayout.addWidget(intervalLabel)
                displacement = QDoubleSpinBox()
                displacement.setFixedWidth(72)
                displacement.setDecimals(1)
                snapLayout.addWidget(displacement)
                DisplacementLabel = QLabel("Displacement")
                DisplacementLabel.setToolTip("Displaces the snap positions by amount")
                snapLayout.addWidget(DisplacementLabel)
                snapGroup.setLayout(snapLayout)
                tabLayout.addWidget(snapGroup)
                
                param = name[len(model):]
                if (model == 'HCY' or model == 'OKHCL') and param != 'Chroma':
                    radioGroup = QGroupBox("Chroma Mode")
                    radioGroup.setFixedHeight(64)
                    radioGroup.setToolTip("Switches how chroma is adjusted \
                                          to stay within the sRGB gamut")
                    radioLayout = QHBoxLayout()
                    clip = QRadioButton("Clip")
                    clip.setToolTip("Clips chroma if it exceeds the srgb gamut when adjusting")
                    radioLayout.addWidget(clip)
                    scale = QRadioButton("Scale")
                    scale.setToolTip("Scales chroma to maintain constant saturation when adjusting")
                    radioLayout.addWidget(scale)
                    if channel.scale:
                        scale.setChecked(True)
                    else:
                        clip.setChecked(True)
                    clip.toggled.connect(channel.clipChroma)
                    radioGroup.setLayout(radioLayout)
                    tabLayout.addWidget(radioGroup)

                    if model == 'HCY' and param == 'Luma':
                        luma = QCheckBox("Always Luma")
                        luma.setToolTip("Transfer components to sRGB in linear TRCs")
                        luma.setChecked(channel.luma)
                        luma.toggled.connect(self.hcl.setLuma)
                        tabLayout.addWidget(luma)

                if param == 'Hue':
                    interval.setMaximum(360.0)
                    interval.setSuffix(u'\N{DEGREE SIGN}')
                    displacement.setMaximum(359.9)
                    displacement.setSuffix(u'\N{DEGREE SIGN}')
                    colorful = QCheckBox("Colorful Gradient")
                    colorful.setToolTip("Gradient colors will always be at max chroma")
                    colorful.setChecked(channel.colorful)
                    colorful.toggled.connect(channel.colorfulHue)
                    tabLayout.addStretch()
                    tabLayout.addWidget(colorful)
                else:
                    interval.setMaximum(100.0)
                    interval.setSuffix('%')
                    displacement.setSuffix('%')

                interval.setValue(channel.slider.interval)
                interval.valueChanged.connect(channel.slider.setInterval)
                displacement.setValue(channel.slider.displacement)
                displacement.valueChanged.connect(channel.slider.setDisplacement)

                tabs.addTab(tab, param)
                checkBox = QCheckBox()
                checkBox.setChecked(not((model in visible) and (name in hidden)))
                tab.setEnabled(checkBox.isChecked())
                self.checkBoxes[name] = checkBox
                tabs.tabBar().setTabButton(tabs.tabBar().count() - 1, 
                                           tabs.tabBar().ButtonPosition.LeftSide, checkBox)
                checkBox.toggled.connect(tab.setEnabled)
                checkBox.stateChanged.connect(self.reorderSliders)

            tabs.tabBar().tabMoved.connect(self.reorderSliders)
            self.pages.addWidget(tabs)
            self.pageList.addItem(model)
            item = self.pageList.item(self.pageList.count() - 1)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked) if model in visible else item.setCheckState(
                Qt.CheckState.Unchecked)
            tabs.setEnabled(item.checkState() == Qt.CheckState.Checked)
        self.pageList.model().rowsMoved.connect(self.reorderSliders)
        self.pageList.itemPressed.connect(self.changePage)
        self.pageList.currentTextChanged.connect(self.changePage)
        self.pageList.itemChanged.connect(self.toggleModel)

        self.others = QPushButton("Others")
        self.others.setAutoDefault(False)
        self.others.setCheckable(True)
        self.others.setFixedWidth(76)
        self.others.clicked.connect(self.changeOthers)

        history = QGroupBox("Color History")
        history.setFixedHeight(64)
        history.setToolTip("Records foreground color when changed")
        history.setCheckable(True)
        history.setChecked(self.hcl.history.isEnabled())
        history.toggled.connect(self.refreshOthers)
        memory = QSpinBox()
        memory.setFixedWidth(72)
        memory.setMaximum(999)
        memory.setValue(self.hcl.memory)
        memory.valueChanged.connect(self.hcl.setMemory)
        memoryLabel = QLabel("Memory")
        memoryLabel.setToolTip("Limits color history, set to 0 for unlimited")
        clearButton = QPushButton("Clear History")
        clearButton.setAutoDefault(False)
        clearButton.setToolTip("Removes all colors in history")
        clearButton.clicked.connect(self.hcl.clearHistory)
        historyLayout = QHBoxLayout()
        historyLayout.addWidget(memory)
        historyLayout.addWidget(memoryLabel)
        historyLayout.addWidget(clearButton)
        history.setLayout(historyLayout)
        syntax = QCheckBox("Color Syntax")
        syntax.setToolTip("Panel for hex/oklab/oklch css syntax")
        syntax.setChecked(self.hcl.syntax.isEnabled())
        syntax.stateChanged.connect(self.refreshOthers)

        othersTab = QWidget()
        pageLayout = QVBoxLayout()
        pageLayout.addSpacing(12)
        pageLayout.addWidget(history)
        pageLayout.addStretch()
        pageLayout.addWidget(syntax)
        pageLayout.addStretch()
        othersTab.setLayout(pageLayout)
        othersPage = QTabWidget()
        othersPage.addTab(othersTab, "Other Settings")
        self.pages.addWidget(othersPage)

        listLayout = QVBoxLayout()
        listLayout.addWidget(self.pageList)
        listLayout.addWidget(self.others)
        self.mainLayout.addLayout(listLayout)
        self.mainLayout.addWidget(self.pages)

    def changePage(self, item: str|QListWidgetItem):
        if isinstance(item, QListWidgetItem):
            item = item.text()
        self.pages.setCurrentIndex(list(self.models.keys()).index(item))
        self.others.setChecked(False)

    def changeOthers(self):
        self.others.setChecked(True)
        self.pages.setCurrentIndex(self.pages.count() - 1)
        self.pageList.clearSelection()

    def refreshOthers(self, state: bool|int):
        # toggled vs stateChanged
        if isinstance(state, bool):
            self.hcl.history.setEnabled(state)
        else:
            state = state == Qt.CheckState.Checked
            self.hcl.syntax.setEnabled(state)
        # Refresh hcl layout
        self.hcl.clearOthers()
        self.hcl.displayOthers()

    def reorderSliders(self):
        # Get new display order
        self.hcl.displayOrder = []
        for row in range(self.pageList.count()):
            item = self.pageList.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                model = item.text()
                tabs = self.pages.widget(list(self.models.keys()).index(model))
                for index in range(tabs.count()):
                    # visible tabs have '&' in text used for shortcut
                    param = tabs.tabText(index).replace('&', '')
                    name = f"{model.lower()}{param}"
                    if self.checkBoxes[name].isChecked():
                        self.hcl.displayOrder.append(name)
        # Refresh channel layout
        self.hcl.clearChannels()
        self.hcl.displayChannels()

    def toggleModel(self, item: QListWidgetItem):
        tabs = self.pages.widget(list(self.models.keys()).index(item.text()))
        tabs.setEnabled(item.checkState() == Qt.CheckState.Checked)
        
        self.reorderSliders()

    def closeEvent(self, event):
        self.hcl.writeSettings()
        event.accept()


class HCLSliders(DockWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(DOCKER_NAME)
        mainWidget = QWidget(self)
        mainWidget.setContentsMargins(2, 1, 2, 1)
        self.setWidget(mainWidget)
        self.mainLayout = QVBoxLayout(mainWidget)
        self.mainLayout.setSpacing(2)
        self.config = None
        self.document = None
        self.memory = 30
        self.trc = "sRGB"
        self.notation = NOTATION[0]
        self.text = ""
        self.pressed = False
        self.editing = False
        self.pastColors = []
        self.loadChannels()
        self.history = ColorHistory(self)
        self.loadSyntax()
        self.readSettings()
        self.displayChannels()
        self.displayOthers()
        self.updateNotations()

    def colorDisplay(self):
        # load into channel layout to prevent alignment issue when channels empty
        layout = QHBoxLayout()
        layout.setSpacing(2)

        self.color = ColorDisplay(self)
        self.color.setFixedHeight(DISPLAY_HEIGHT)
        layout.addWidget(self.color)

        button = QPushButton()
        button.setIcon(Application.icon('configure'))
        button.setFlat(True)
        button.setFixedSize(DISPLAY_HEIGHT, DISPLAY_HEIGHT)
        button.setIconSize(QSize(DISPLAY_HEIGHT - 2, DISPLAY_HEIGHT - 2))
        button.setToolTip("Configure HCL Sliders")
        button.clicked.connect(self.openConfig)
        layout.addWidget(button)

        self.timer = QTimer()
        self.timer.timeout.connect(self.getKritaColors)
        self.singleShot = QTimer()
        self.singleShot.setSingleShot(True)
        self.singleShot.timeout.connect(self.setHistory)
        return layout
    
    def loadChannels(self):
        self.channelLayout = QVBoxLayout()
        self.channelLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.channelLayout.setSpacing(2)
        self.channelLayout.addLayout(self.colorDisplay())
        self.channelLayout.addSpacing(1)

        self.hsvHue = ColorChannel("hsvHue", self)
        self.hsvSaturation = ColorChannel("hsvSaturation", self)
        self.hsvValue = ColorChannel("hsvValue", self)

        self.hslHue = ColorChannel("hslHue", self)
        self.hslSaturation = ColorChannel("hslSaturation", self)
        self.hslLightness = ColorChannel("hslLightness", self)

        self.hcyHue = ColorChannel("hcyHue", self)
        self.hcyHue.scale = False
        self.hcyChroma = ColorChannel("hcyChroma", self)
        self.hcyLuma = ColorChannel("hcyLuma", self)
        self.hcyLuma.scale = False

        self.okhclHue = ColorChannel("okhclHue", self)
        self.okhclHue.scale = False
        self.okhclChroma = ColorChannel("okhclChroma", self)
        self.okhclLightness = ColorChannel("okhclLightness", self)
        self.okhclLightness.scale = False

        self.okhsvHue = ColorChannel("okhsvHue", self)
        self.okhsvSaturation = ColorChannel("okhsvSaturation", self)
        self.okhsvValue = ColorChannel("okhsvValue", self)

        self.okhslHue = ColorChannel("okhslHue", self)
        self.okhslSaturation = ColorChannel("okhslSaturation", self)
        self.okhslLightness = ColorChannel("okhslLightness", self)
        
        self.mainLayout.addLayout(self.channelLayout)

    def loadSyntax(self):
        self.prevNotation = QPushButton()
        self.prevNotation.setFlat(True)
        self.prevNotation.setFixedSize(CHANNEL_HEIGHT - 1, CHANNEL_HEIGHT - 1)
        self.prevNotation.setIcon(Application.icon('arrow-left'))
        self.prevNotation.setIconSize(QSize(CHANNEL_HEIGHT - 5, CHANNEL_HEIGHT - 5))
        self.prevNotation.clicked.connect(self.switchNotation)

        self.nextNotation = QPushButton()
        self.nextNotation.setFlat(True)
        self.nextNotation.setFixedSize(CHANNEL_HEIGHT - 1, CHANNEL_HEIGHT - 1)
        self.nextNotation.setIcon(Application.icon('arrow-right'))
        self.nextNotation.setIconSize(QSize(CHANNEL_HEIGHT - 5, CHANNEL_HEIGHT - 5))
        self.nextNotation.clicked.connect(self.switchNotation)

        self.syntax = QLineEdit()
        self.syntax.setFixedHeight(CHANNEL_HEIGHT - 1)
        self.syntax.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.syntax.editingFinished.connect(self.parseSyntax)

    def readSettings(self):
        channels = ColorChannel.getList()
        for name in channels:
            settings: list = Application.readSetting(DOCKER_NAME, name, "").split(",")
            print(settings)
            if len(settings) > 1:
                channel: ColorChannel = getattr(self, name)
                try:
                    channel.slider.setInterval(float(settings[0]))
                except ValueError:
                    print(f"Invalid interval amount for {name}")
                
                try:
                    channel.slider.setDisplacement(float(settings[1]))
                except ValueError:
                    print(f"Invalid displacement amount for {name}")

                if (name[:3] == "hcy" or name[:5] == "okhcl") and name[-6:] != "Chroma":
                    channel.scale = settings[2] == "True"

                if name[-3:] == "Hue":
                    if len(settings) > 3:
                        channel.colorful = settings[3] == "True"
                    else:
                        channel.colorful = settings[2] == "True"

                if name[:3] == "hcy":
                    channel.luma = settings[-1] == "True"
        
        self.displayOrder = []
        displayed = Application.readSetting(DOCKER_NAME, "displayed", "").split(",")
        for name in displayed:
            if name in channels:
                self.displayOrder.append(name)
        if not self.displayOrder:
            self.displayOrder = channels

        history = Application.readSetting(DOCKER_NAME, "history", "").split(",")
        if len(history) == 2:
            self.history.setEnabled(history[0] != "False")
            try:
                memory = int(history[1])
                if 0 <= memory <= 999:
                    self.memory = memory
            except ValueError:
                ("Invalid memory value")
        
        syntax = Application.readSetting(DOCKER_NAME, "syntax", "").split(",")
        if len(syntax) == 2:
            self.syntax.setEnabled(syntax[0] != "False")
            notation = syntax[1]
            if notation in NOTATION:
                self.notation = notation

    def writeSettings(self):
        Application.writeSetting(DOCKER_NAME, "displayed", ",".join(self.displayOrder))

        for name in ColorChannel.getList():
            settings = []
            channel: ColorChannel = getattr(self, name)
            settings.append(str(channel.slider.interval))
            settings.append(str(channel.slider.displacement))

            if (name[:3] == "hcy" or name[:5] == "okhcl") and name[-6:] != "Chroma":
                settings.append(str(channel.scale))
            if name[-3:] == "Hue":
                settings.append(str(channel.colorful))
            if name[:3] == "hcy":
                settings.append(str(channel.luma))
            
            Application.writeSetting(DOCKER_NAME, name, ",".join(settings))

        history = [str(self.history.isEnabled()), str(self.memory)]
        Application.writeSetting(DOCKER_NAME, "history", ",".join(history))

        syntax = [str(self.syntax.isEnabled()), self.notation]
        Application.writeSetting(DOCKER_NAME, "syntax", ",".join(syntax))

    def displayChannels(self):
        for name in self.displayOrder:
            channel = getattr(self, name)
            channel.layout.addWidget(channel.label)
            channel.layout.addWidget(channel.slider)
            channel.layout.addWidget(channel.spinBox)
            self.channelLayout.addLayout(channel.layout)

    def clearChannels(self):
        # first 2 items in channelLayout is color display and spacing
        for i in reversed(range(self.channelLayout.count() - 2)):
            item = self.channelLayout.itemAt(i + 2)
            layout = item.layout()
            for index in reversed(range(layout.count())):
                widget = layout.itemAt(index).widget()
                layout.removeWidget(widget)
                widget.setParent(None)
            self.channelLayout.removeItem(item)

    def displayOthers(self):
        if self.history.isEnabled():
            self.mainLayout.addSpacing(1)
            self.mainLayout.addWidget(self.history)
        if self.syntax.isEnabled():
            self.mainLayout.addSpacing(1)
            syntaxLayout = QHBoxLayout()
            syntaxLayout.addWidget(self.prevNotation)
            syntaxLayout.addWidget(self.syntax)
            syntaxLayout.addWidget(self.nextNotation)
            self.mainLayout.addLayout(syntaxLayout)

    def clearOthers(self):
        # first item in mainLayout is channelLayout
        for i in reversed(range(self.mainLayout.count() - 1)):
            item = self.mainLayout.itemAt(i + 1)
            widget = item.widget()
            if widget:
                self.mainLayout.removeWidget(widget)
                widget.setParent(None)
            else:
                layout = item.layout()
                if layout:
                    for index in reversed(range(layout.count())):
                        widget = layout.itemAt(index).widget()
                        layout.removeWidget(widget)
                        widget.setParent(None)
                self.mainLayout.removeItem(item)

    def openConfig(self):
        if self.config is None:
            self.config = SliderConfig(self)
        self.config.show()

    def profileTRC(self, profile: str):
        if profile in SRGB:
            return "sRGB"
        elif profile in LINEAR:
            return "linear"
        print("Incompatible profile")
        return self.trc
    
    def setMemory(self, memory: int):
        self.memory = memory

    def setPressed(self, pressed: bool):
        self.pressed = pressed

    def finishEditing(self):
        self.editing = False

    def getKritaColors(self):
        view = Application.activeWindow().activeView()
        if not view.visible():
            return

        if not self.pressed and not self.editing:
            # add to color history after slider sets color
            if self.color.isChanged() and self.color.current:
                self.setHistory()

            foreground = view.foregroundColor()
            self.color.setForeGroundColor(foreground)

            if self.color.isChanged():
                self.color.setCurrentColor(foreground)
                rgb = tuple(foreground.componentsOrdered()[:3])
                trc = self.profileTRC(foreground.colorProfile())
                self.updateSyntax(rgb, trc)          
                if trc != self.trc:
                    rgb = Convert.rgbToTRC(rgb, self.trc)
                self.updateChannels(rgb)
                # add to color history after krita changes color
                if not self.singleShot.isActive():
                    self.color.recent = foreground
                    self.singleShot.start(DELAY)

    def blockChannels(self, block: bool):
        # hsv
        self.hsvHue.blockSignals(block)
        self.hsvSaturation.blockSignals(block)
        self.hsvValue.blockSignals(block)
        # hsl
        self.hslHue.blockSignals(block)
        self.hslSaturation.blockSignals(block)
        self.hslLightness.blockSignals(block)
        # hcy
        self.hcyHue.blockSignals(block)
        self.hcyChroma.blockSignals(block)
        self.hcyLuma.blockSignals(block)
        # okhcl
        self.okhclHue.blockSignals(block)
        self.okhclChroma.blockSignals(block)
        self.okhclLightness.blockSignals(block)
        # okhsv
        self.okhsvHue.blockSignals(block)
        self.okhsvSaturation.blockSignals(block)
        self.okhsvValue.blockSignals(block)
        # okhsl
        self.okhslHue.blockSignals(block)
        self.okhslSaturation.blockSignals(block)
        self.okhslLightness.blockSignals(block)

    def updateChannels(self, values: tuple|float, name: str=None, widget: str=None):
        self.timer.stop()
        self.blockChannels(True)
        
        if type(values) is tuple:
            # update color from krita that is not adjusted by this plugin
            self.setChannelValues("hsv", values)
            self.setChannelValues("hsl", values)
            self.setChannelValues("hcy", values)
            self.setChannelValues("okhcl", values)
            self.setChannelValues("okhsv", values)
            self.setChannelValues("okhsl", values)
        else:
            # update slider if spinbox adjusted vice versa
            channel: ColorChannel = getattr(self, name)
            channelWidget = getattr(channel, widget)
            channelWidget.setValue(values)
            if widget == "slider":
                # prevent getKritaColors when still editing spinBox
                self.editing = True
            # adjusting hsv sliders
            if name[:3] == "hsv":
                hue = self.hsvHue.value()
                rgb = Convert.hsvToRgbF(hue, self.hsvSaturation.value(), 
                                        self.hsvValue.value(), self.trc)
                self.setKritaFGColor(rgb)
                self.setChannelValues("hsl", rgb, hue)
                if self.hcyLuma.luma or self.trc == "sRGB":
                    self.setChannelValues("hcy", rgb, hue)
                else: 
                    self.setChannelValues("hcy", rgb)
                self.setChannelValues("okhcl", rgb)
                self.setChannelValues("okhsv", rgb)
                self.setChannelValues("okhsl", rgb)
            # adjusting hsl sliders
            elif name[:3] == "hsl":
                hue = self.hslHue.value()
                rgb = Convert.hslToRgbF(hue, self.hslSaturation.value(), 
                                        self.hslLightness.value(), self.trc)
                self.setKritaFGColor(rgb)
                self.setChannelValues("hsv", rgb, hue)
                if self.hcyLuma.luma or self.trc == "sRGB":
                    self.setChannelValues("hcy", rgb, hue)
                else:
                    self.setChannelValues("hcy", rgb)
                self.setChannelValues("okhcl", rgb)
                self.setChannelValues("okhsv", rgb)
                self.setChannelValues("okhsl", rgb)
            # adjusting hcy sliders
            elif name[:3] == "hcy":
                hue = self.hcyHue.value()
                chroma = self.hcyChroma.value()
                limit = -1
                if channel.scale:
                    if self.hcyChroma.limit > 0:
                        self.hcyChroma.clip = chroma
                    limit = self.hcyChroma.limit
                else:
                    if self.hcyChroma.clip == 0:
                        self.hcyChroma.clip = chroma
                    else:
                        chroma = self.hcyChroma.clip
                rgb = Convert.hcyToRgbF(hue, chroma, self.hcyLuma.value(), 
                                        limit, self.trc, channel.luma)
                self.setKritaFGColor(rgb)
                if name[-6:] != "Chroma":
                    hcy = Convert.rgbFToHcy(*rgb, hue, self.trc, channel.luma)
                    self.hcyChroma.setLimit(hcy[3])
                    self.hcyChroma.setValue(hcy[1])
                # relative luminance doesnt match luma in hue
                if channel.luma or self.trc == "sRGB":
                    self.setChannelValues("hsv", rgb, hue)
                    self.setChannelValues("hsl", rgb, hue)
                else:
                    self.setChannelValues("hsv", rgb)
                    self.setChannelValues("hsl", rgb)
                self.setChannelValues("okhcl", rgb)
                self.setChannelValues("okhsv", rgb)
                self.setChannelValues("okhsl", rgb)
            # adjusting okhcl sliders
            elif name[:5] == "okhcl":
                hue = self.okhclHue.value()
                chroma = self.okhclChroma.value()
                limit = -1
                if channel.scale:
                    if self.okhclChroma.limit > 0:
                        self.okhclChroma.clip = chroma
                    limit = self.okhclChroma.limit
                else:
                    if self.okhclChroma.clip == 0:
                        self.okhclChroma.clip = chroma
                    else:
                        chroma = self.okhclChroma.clip
                rgb = Convert.okhclToRgbF(hue, chroma, self.okhclLightness.value(), limit, self.trc)
                self.setKritaFGColor(rgb)
                if name[-6:] != "Chroma":
                    okhcl = Convert.rgbFToOkhcl(*rgb, hue, self.trc)
                    self.okhclChroma.setLimit(okhcl[3])
                    self.okhclChroma.setValue(okhcl[1])
                self.setChannelValues("hsv", rgb)
                self.setChannelValues("hsl", rgb)
                self.setChannelValues("hcy", rgb)
                self.setChannelValues("okhsv", rgb, hue)
                self.setChannelValues("okhsl", rgb, hue)
            # adjusting okhsv sliders
            elif name[:5] == "okhsv":
                hue = self.okhsvHue.value()
                rgb = Convert.okhsvToRgbF(hue, self.okhsvSaturation.value(), 
                                          self.okhsvValue.value(), self.trc)
                self.setKritaFGColor(rgb)
                self.setChannelValues("hsv", rgb)
                self.setChannelValues("hsl", rgb)
                self.setChannelValues("hcy", rgb)
                self.setChannelValues("okhcl", rgb, hue)
                self.setChannelValues("okhsl", rgb, hue)
            # adjusting okhsl sliders
            elif name[:5] == "okhsl":
                hue = self.okhslHue.value()
                rgb = Convert.okhslToRgbF(hue, self.okhslSaturation.value(), 
                                          self.okhslLightness.value(), self.trc)
                self.setKritaFGColor(rgb)
                self.setChannelValues("hsv", rgb)
                self.setChannelValues("hsl", rgb)
                self.setChannelValues("hcy", rgb)
                self.setChannelValues("okhcl", rgb, hue)
                self.setChannelValues("okhsv", rgb, hue)
        
        self.updateChannelGradients()
        self.blockChannels(False)
        if TIME:
            self.timer.start(TIME)

    def updateChannelGradients(self, channels: str=None):
        if not channels or channels == "hsv":
            self.hsvHue.updateGradientColors(self.hsvSaturation.value(), self.hsvValue.value(), 
                                             self.trc)
            self.hsvSaturation.updateGradientColors(self.hsvHue.value(), self.hsvValue.value(), 
                                                    self.trc)
            self.hsvValue.updateGradientColors(self.hsvHue.value(), self.hsvSaturation.value(), 
                                               self.trc)
        if not channels or channels == "hsl":
            self.hslHue.updateGradientColors(self.hslSaturation.value(), self.hslLightness.value(), 
                                             self.trc)
            self.hslSaturation.updateGradientColors(self.hslHue.value(), self.hslLightness.value(), 
                                                    self.trc)
            self.hslLightness.updateGradientColors(self.hslHue.value(), self.hslSaturation.value(), 
                                                   self.trc)
        if not channels or channels == "hcy":
            hcyClip = self.hcyChroma.value()
            if self.hcyChroma.clip > 0:
                hcyClip = self.hcyChroma.clip
            if self.hcyHue.scale:
                self.hcyHue.updateGradientColors(self.hcyChroma.value(), self.hcyLuma.value(), 
                                                 self.trc, self.hcyChroma.limit)
            else:
                self.hcyHue.updateGradientColors(hcyClip, self.hcyLuma.value(), self.trc)
            self.hcyChroma.updateGradientColors(self.hcyHue.value(), self.hcyLuma.value(), 
                                                self.trc, self.hcyChroma.limit)
            if self.hcyLuma.scale:
                self.hcyLuma.updateGradientColors(self.hcyHue.value(), self.hcyChroma.value(), 
                                                  self.trc, self.hcyChroma.limit)
            else:
                self.hcyLuma.updateGradientColors(self.hcyHue.value(), hcyClip, self.trc)
        if not channels or channels == "okhcl":
            okhclClip = self.okhclChroma.value()
            if self.okhclChroma.clip > 0:
                okhclClip = self.okhclChroma.clip
            if self.okhclHue.scale:
                self.okhclHue.updateGradientColors(self.okhclChroma.value(), self.okhclLightness.value(), 
                                                   self.trc, self.okhclChroma.limit)
            else:
                self.okhclHue.updateGradientColors(okhclClip, self.okhclLightness.value(), self.trc)
            self.okhclChroma.updateGradientColors(self.okhclHue.value(), self.okhclLightness.value(), 
                                                  self.trc, self.okhclChroma.limit)
            if self.okhclLightness.scale:
                self.okhclLightness.updateGradientColors(self.okhclHue.value(), self.okhclChroma.value(), 
                                                         self.trc, self.okhclChroma.limit)
            else:
                self.okhclLightness.updateGradientColors(self.okhclHue.value(), okhclClip, self.trc)
        if not channels or channels == "okhsv":
            self.okhsvHue.updateGradientColors(self.okhsvSaturation.value(), 
                                               self.okhsvValue.value(), self.trc)
            self.okhsvSaturation.updateGradientColors(self.okhsvHue.value(), 
                                                      self.okhsvValue.value(), self.trc)
            self.okhsvValue.updateGradientColors(self.okhsvHue.value(), 
                                                 self.okhsvSaturation.value(), self.trc)
        if not channels or channels == "okhsl":
            self.okhslHue.updateGradientColors(self.okhslSaturation.value(), 
                                               self.okhslLightness.value(), self.trc)
            self.okhslSaturation.updateGradientColors(self.okhslHue.value(), 
                                                      self.okhslLightness.value(), self.trc)
            self.okhslLightness.updateGradientColors(self.okhslHue.value(), 
                                                     self.okhslSaturation.value(), self.trc)

    def setChannelValues(self, channels: str, rgb: tuple, hue: float=-1):
        if channels == "hsv":
            hsv = Convert.rgbFToHsv(*rgb, self.trc)
            if hue != -1:
                self.hsvHue.setValue(hue)
            if hsv[2] == 0:
                self.hsvValue.setValue(0)
            elif hsv[1] == 0:
                self.hsvSaturation.setValue(0)
                self.hsvValue.setValue(hsv[2])
            else:
                if hue == -1:
                    self.hsvHue.setValue(hsv[0])
                self.hsvSaturation.setValue(hsv[1])
                self.hsvValue.setValue(hsv[2])
        elif channels == "hsl":
            hsl = Convert.rgbFToHsl(*rgb, self.trc)
            if hue != -1:
                self.hslHue.setValue(hue)
            if hsl[2] == 0 or hsl[2] == 1:
                self.hslLightness.setValue(hsl[2])
            elif hsl[1] == 0:
                self.hslSaturation.setValue(0)
                self.hslLightness.setValue(hsl[2])
            else:
                if hue == -1:
                    self.hslHue.setValue(hsl[0])
                self.hslSaturation.setValue(hsl[1])
                self.hslLightness.setValue(hsl[2])
        elif channels == "hcy":
            self.hcyChroma.clip = 0.0
            hcy = Convert.rgbFToHcy(*rgb, self.hcyHue.value(), self.trc, self.hcyLuma.luma)
            if hue != -1:
                self.hcyHue.setValue(hue)
            if hcy[1] == 0:
                self.hcyChroma.setLimit(hcy[3])
                self.hcyChroma.setValue(hcy[1])
                self.hcyLuma.setValue(hcy[2])
            else:
                if hue == -1:
                    self.hcyHue.setValue(hcy[0])
                # must always set limit before setting chroma value
                self.hcyChroma.setLimit(hcy[3])
                self.hcyChroma.setValue(hcy[1])
                self.hcyLuma.setValue(hcy[2])
        elif channels == "okhcl":
            self.okhclChroma.clip = 0.0
            okhcl = Convert.rgbFToOkhcl(*rgb, self.okhclHue.value(), self.trc)
            if hue != -1:
                self.okhclHue.setValue(hue)
            else:
                self.okhclHue.setValue(okhcl[0])
            # must always set limit before setting chroma value
            self.okhclChroma.setLimit(okhcl[3])
            self.okhclChroma.setValue(okhcl[1])
            self.okhclLightness.setValue(okhcl[2])
        elif channels == "okhsv":
            okhsv = Convert.rgbFToOkhsv(*rgb, self.trc)
            if hue != -1:
                self.okhsvHue.setValue(hue)
            if okhsv[2] == 0:
                self.okhsvValue.setValue(0)
            elif okhsv[1] == 0:
                self.okhsvSaturation.setValue(0)
                self.okhsvValue.setValue(okhsv[2])
            else:
                if hue == -1:
                    self.okhsvHue.setValue(okhsv[0])
                self.okhsvSaturation.setValue(okhsv[1])
                self.okhsvValue.setValue(okhsv[2])
        elif channels == "okhsl":
            okhsl = Convert.rgbFToOkhsl(*rgb, self.trc)
            if hue != -1:
                self.okhslHue.setValue(hue)
            if okhsl[2] == 0 or okhsl[2] == 1:
                self.okhslLightness.setValue(okhsl[2])
            elif okhsl[1] == 0:
                self.okhslSaturation.setValue(0)
                self.okhslLightness.setValue(okhsl[2])
            else:
                if hue == -1:
                    self.okhslHue.setValue(okhsl[0])
                self.okhslSaturation.setValue(okhsl[1])
                self.okhslLightness.setValue(okhsl[2])

    def makeManagedColor(self, rgb: tuple, profile: str=None):
        model = self.document.colorModel()
        # support for other models in the future
        if model == "RGBA":
            if not profile:
                profile = self.document.colorProfile()
            color = ManagedColor(model, self.document.colorDepth(), profile)
            components = color.components()
            # unordered sequence is BGRA
            components[0] = rgb[2]
            components[1] = rgb[1]
            components[2] = rgb[0]
            components[3] = 1.0

            color.setComponents(components)
            return color

    def setKritaFGColor(self, rgb: tuple):
        view = Application.activeWindow().activeView()
        if not view.visible():
            return
        
        color = self.makeManagedColor(rgb)
        self.color.setCurrentColor(color)
        self.updateSyntax(rgb, self.trc)
        view.setForeGroundColor(color)
        self.color.recent = color

    def setLuma(self, luma: bool):
        self.timer.stop()
        self.blockChannels(True)

        self.hcyHue.luma = luma
        self.hcyChroma.luma = luma
        self.hcyLuma.luma = luma

        if self.color.foreground:
            rgb = tuple(self.color.foreground.componentsOrdered()[:3])
            trc = self.profileTRC(self.color.foreground.colorProfile())    
            if trc != self.trc:
                rgb = Convert.rgbToTRC(rgb, self.trc)
            if luma or self.trc == "sRGB":
                self.setChannelValues("hcy", rgb, self.hsvHue.value())
            else:
                self.setChannelValues("hcy", rgb)
            self.updateChannelGradients("hcy")

        self.blockChannels(False)
        if TIME:
            self.timer.start(TIME)

    def setHistory(self):
        if self.color.isChanging():
            # allow getKritaColors to start timer for set history
            self.color.current = None
            return
        
        rgb = tuple(self.color.current.componentsOrdered()[:3])
        profile = self.color.current.colorProfile()
        color = (rgb, profile)
        if color in self.pastColors:
            index = self.pastColors.index(color)
            if index:
                self.pastColors.pop(index)
                self.pastColors.insert(0, color)
                item = self.history.takeItem(index)
                self.history.insertItem(0, item)
        else:
            self.pastColors.insert(0, color)
            pixmap = QPixmap(HISTORY_HEIGHT, HISTORY_HEIGHT)
            pixmap.fill(QColor(*Convert.rgbFToInt8(*rgb, self.profileTRC(profile))))
            item = QListWidgetItem()
            item.setIcon(QIcon(pixmap))
            self.history.insertItem(0, item)
            if self.memory:
                for i in reversed(range(self.history.count())):
                    if i > self.memory - 1:
                        self.history.takeItem(i)
                        self.pastColors.pop()
                    else:
                        break
        self.history.horizontalScrollBar().setValue(0)

    def setPastColorToFG(self, index: int):
        view = Application.activeWindow().activeView()
        if not view.visible():
            return
        
        self.history.takeItem(index)
        color = self.pastColors.pop(index)
        rgb = color[0]
        trc = self.profileTRC(color[1])
        self.updateSyntax(rgb, trc)
        if trc != self.trc:
            rgb = Convert.rgbToTRC(rgb, self.trc)
        self.updateChannels(rgb)
        view.setForeGroundColor(self.color.current)
        # prevent setHistory again during getKritaColors
        self.color.setForeGroundColor(self.color.current)
        self.color.recent = self.color.current
        self.setHistory()

    def setPastColorToBG(self):
        view = Application.activeWindow().activeView()
        if not view.visible():
            return
        
        view.setBackGroundColor(self.color.background)

    def clearHistory(self):
        self.history.clear()
        self.pastColors = []
    
    def updateSyntax(self, rgb: tuple, trc: str):
        if self.notation == NOTATION[0]:
            self.text = Convert.rgbFToHexS(*rgb, trc)
        elif self.notation == NOTATION[1]:
            self.text = Convert.rgbFToOklabS(*rgb, trc)
        elif self.notation == NOTATION[2]:
            self.text = Convert.rgbFToOklchS(*rgb, trc)
        self.syntax.setText(self.text)

    def switchNotation(self):
        view = Application.activeWindow().activeView()
        if not view.visible():
            return
        
        notation = self.sender().toolTip()
        self.setNotation(notation)
        self.updateNotations()
        color = view.foregroundColor()
        trc = self.profileTRC(color.colorProfile())
        self.updateSyntax(color.componentsOrdered()[:3], trc)

    def setNotation(self, notation: str):
        self.notation = notation
        # syntax needs to be on to set notation currently
        Application.writeSetting(DOCKER_NAME, "syntax", ",".join(["True", notation]))

    def updateNotations(self):
        i = NOTATION.index(self.notation)
        if i == 0:
            self.prevNotation.setToolTip(NOTATION[len(NOTATION) - 1])
            self.nextNotation.setToolTip(NOTATION[i + 1])
        elif i == len(NOTATION) - 1:
            self.prevNotation.setToolTip(NOTATION[i - 1])
            self.nextNotation.setToolTip(NOTATION[0])
        else:
            self.prevNotation.setToolTip(NOTATION[i - 1])
            self.nextNotation.setToolTip(NOTATION[i + 1])

    def parseSyntax(self):
        view = Application.activeWindow().activeView()
        if not view.visible():
            return
        syntax = self.syntax.text().strip()
        if syntax == self.text:
            return

        rgb = None
        notation = self.notation
        if syntax[:1] == "#":
            self.setNotation(NOTATION[0])
            rgb = Convert.hexSToRgbF(syntax, self.trc)
        elif syntax[:5].upper() == NOTATION[1]:
            self.setNotation(NOTATION[1])
            rgb = Convert.oklabSToRgbF(syntax, self.trc)
        elif syntax[:5].upper() == NOTATION[2]:
            self.setNotation(NOTATION[2])
            rgb = Convert.oklchSToRgbF(syntax, self.trc)
        
        if notation != self.notation:
            self.updateNotations()
        if rgb:
            self.setKritaFGColor(rgb)
            self.updateChannels(rgb)
        else:
            color = view.foregroundColor()
            trc = self.profileTRC(color.colorProfile())
            self.updateSyntax(color.componentsOrdered()[:3], trc)    
    
    def showEvent(self, event):
        if TIME:
            self.timer.start(TIME)

    def closeEvent(self, event):
        self.timer.stop()

    def canvasChanged(self, canvas):
        if self.document != Application.activeDocument():
            self.document = Application.activeDocument()
            self.trc = self.profileTRC(self.document.colorProfile())
            self.color.resetColors()
            self.syntax.setText("")
            self.getKritaColors()

