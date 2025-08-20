# SPDX-License-Identifier: GPL-3.0-or-later AND MIT
#
# Color conversion script for python.
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
#   Copyright (c) 2021 Björn Ottosson
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of
#   this software and associated documentation files (the "Software"), to deal in
#   the Software without restriction, including without limitation the rights to
#   use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
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

import math, sys
from .settings import *
# luma coefficents for ITU-R BT.709
Y709R = 0.2126
Y709G = 0.7152
Y709B = 0.0722
# constants for sRGB transfer 
ALPHA = 0.055
GAMMA = 2.4
PHI = 12.92
# toe functions
K1 = 0.206
K2 = 0.03
K3 = (1.0 + K1) / (1.0 + K2)


class Convert:

    @staticmethod
    def roundZero(n: float, d: int):
        s = -1 if n < 0 else 1
        if not isinstance(d, int):
            raise TypeError("decimal places must be an integer")
        elif d < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif d == 0:
            return math.floor(abs(n)) * s
        
        f = 10 ** d
        return math.floor(abs(n) * f) / f * s
    
    @staticmethod
    def clampF(f: float, u: float=1, l: float=0):
        # red may be negative in parts of blue due to color being out of gamut
        if f < l:
            return l
        # round up near 1 and prevent going over 1 from oklab conversion
        if (u == 1 and f > 0.999999) or f > u:
            return u
        return f

    @staticmethod
    def componentToSRGB(c: float):
        # round(CHI / PHI, 7) = 0.0031308
        return (1 + ALPHA) * c ** (1 / GAMMA) - ALPHA if c > 0.0031308 else c * PHI

    @staticmethod
    def componentToLinear(c: float):
        # CHI = 0.04045
        return ((c + ALPHA) / (1 + ALPHA)) ** GAMMA if c > 0.04045 else c / PHI

    @staticmethod
    def cartesianToPolar(a: float, b: float):
        c = math.hypot(a, b)
        hRad = math.atan2(b, a)
        if hRad < 0:
            hRad += math.pi * 2
        h = math.degrees(hRad)
        return (c, h)
    
    @staticmethod
    def polarToCartesian(c: float, h: float):
        hRad = math.radians(h)
        a = c * math.cos(hRad)
        b = c * math.sin(hRad)
        return (a, b)
    
    @staticmethod
    def linearToOklab(r: float, g: float, b: float):
        # convert to approximate cone responses
        #l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
        l = 0.412221469470763 * r + 0.5363325372617348 * g + 0.0514459932675022 * b
        #m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
        m = 0.2119034958178252 * r + 0.6806995506452344 * g + 0.1073969535369406 * b
        #s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
        s = 0.0883024591900564 * r + 0.2817188391361215 * g + 0.6299787016738222 * b
        # apply non-linearity
        l_ = l ** (1 / 3)
        m_ = m ** (1 / 3)
        s_ = s ** (1 / 3)
        # transform to Lab coordinates
        #okL = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
        okL = 0.210454268309314 * l_ + 0.7936177747023054 * m_ - 0.0040720430116193 * s_
        #okA = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
        okA = 1.9779985324311684 * l_ - 2.4285922420485799 * m_ + 0.450593709617411 * s_
        #okB = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
        okB = 0.0259040424655478 * l_ + 0.7827717124575296 * m_ - 0.8086757549230774 * s_
        return (okL, okA, okB)
    
    @staticmethod
    def oklabToLinear(okL: float, okA: float, okB: float):
        # inverse coordinates
        #l_ = okL + 0.3963377774 * okA + 0.2158037573 * okB
        l_ = okL + 0.3963377773761749 * okA + 0.2158037573099136 * okB
        #m_ = okL - 0.1055613458 * okA - 0.0638541728 * okB
        m_ = okL - 0.1055613458156586 * okA - 0.0638541728258133 * okB
        #s_ = okL - 0.0894841775 * okA - 1.2914855480 * okB
        s_ = okL - 0.0894841775298119 * okA - 1.2914855480194092 * okB
        # reverse non-linearity
        l = l_ * l_ * l_
        m = m_ * m_ * m_
        s = s_ * s_ * s_
        # convert to linear rgb
        #r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
        r = +4.0767416360759574 * l - 3.3077115392580616 * m + 0.2309699031821044 * s
        #g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
        g = -1.2684379732850317 * l + 2.6097573492876887 * m - 0.3413193760026573 * s
        #b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
        b = -0.0041960761386756 * l - 0.7034186179359362 * m + 1.7076146940746117 * s
        return(r, g, b)
    
    @staticmethod
    # toe function for L_r
    def toe(x):
        return 0.5 * (K3 * x - K1 + ((K3 * x - K1) * (K3 * x - K1) + 4 * K2 * K3 * x) ** (1 / 2))
    
    @staticmethod
    # inverse toe function for L_r
    def toeInv(x):
        return (x * x + K1 * x) / (K3 * (x + K2))
    
    @staticmethod
    # Finds the maximum saturation possible for a given hue that fits in sRGB
    # Saturation here is defined as S = C/L
    # a and b must be normalized so a^2 + b^2 == 1
    def computeMaxSaturation(a: float, b: float):
        # Max saturation will be when one of r, g or b goes below zero.
        # Select different coefficients depending on which component goes below zero first
        # Blue component
        k0 = +1.35733652
        k1 = -0.00915799 
        k2 = -1.15130210 
        k3 = -0.50559606 
        k4 = +0.00692167
        wl = -0.0041960863 
        wm = -0.7034186147 
        ws = +1.7076147010
        if -1.88170328 * a - 0.80936493 * b > 1:
            # Red component
            k0 = +1.19086277 
            k1 = +1.76576728
            k2 = +0.59662641
            k3 = +0.75515197
            k4 = +0.56771245
            wl = +4.0767416621
            wm = -3.3077115913 
            ws = +0.2309699292
        elif 1.81444104 * a - 1.19445276 * b > 1:
            # Green component
            k0 = +0.73956515 
            k1 = -0.45954404 
            k2 = +0.08285427 
            k3 = +0.12541070 
            k4 = +0.14503204
            wl = -1.2684380046 
            wm = +2.6097574011 
            ws = -0.3413193965
        # Approximate max saturation using a polynomial:
        maxS = k0 + k1 * a + k2 * b + k3 * a * a + k4 * a * b
        # Do one step Halley's method to get closer
        # this gives an error less than 10e6, 
        # except for some blue hues where the dS/dh is close to infinite
        # this should be sufficient for most applications, otherwise do two/three steps 
        k_l = +0.3963377774 * a + 0.2158037573 * b
        k_m = -0.1055613458 * a - 0.0638541728 * b
        k_s = -0.0894841775 * a - 1.2914855480 * b

        l_ = 1.0 + maxS * k_l
        m_ = 1.0 + maxS * k_m
        s_ = 1.0 + maxS * k_s

        l = l_ * l_ * l_
        m = m_ * m_ * m_
        s = s_ * s_ * s_

        l_dS = 3.0 * k_l * l_ * l_
        m_dS = 3.0 * k_m * m_ * m_
        s_dS = 3.0 * k_s * s_ * s_

        l_dS2 = 6.0 * k_l * k_l * l_
        m_dS2 = 6.0 * k_m * k_m * m_
        s_dS2 = 6.0 * k_s * k_s * s_

        f  = wl * l     + wm * m     + ws * s
        f1 = wl * l_dS  + wm * m_dS  + ws * s_dS
        f2 = wl * l_dS2 + wm * m_dS2 + ws * s_dS2

        maxS = maxS - f * f1 / (f1*f1 - 0.5 * f * f2)
        return maxS
    
    @staticmethod
    # finds L_cusp and C_cusp for a given hue
    # a and b must be normalized so a^2 + b^2 == 1
    def findCuspLC(a: float, b: float):
        # First, find the maximum saturation (saturation S = C/L)
        maxS = Convert.computeMaxSaturation(a, b)
        # Convert to linear sRGB to find the first point where at least one of r,g or b >= 1:
        maxRgb = Convert.oklabToLinear(1, maxS * a, maxS * b)
        cuspL = (1.0 / max(maxRgb[0], maxRgb[1], maxRgb[2])) ** (1 / 3)
        cuspC = cuspL * maxS
        return (cuspL, cuspC)
    
    @staticmethod
    # Finds intersection of the line defined by 
    # L = L0 * (1 - t) + t * L1
    # C = t * C1
    # a and b must be normalized so a^2 + b^2 == 1
    def findGamutIntersection(a: float, b: float, l1: float, c1: float, l0: float, cuspLC=None):
        # Find the cusp of the gamut triangle
        if cuspLC is None:
            cuspLC = Convert.findCuspLC(a, b)
        # Find the intersection for upper and lower half separately
        if ((l1 - l0) * cuspLC[1] - (cuspLC[0] - l1) * c1) <= 0.0:
            # Lower half
            t = cuspLC[1] * l0 / (c1 * cuspLC[0] + cuspLC[1] * (l0 - l1))
        else:
            # Upper half
            # First intersect with triangle
            t = cuspLC[1] * (l0 - 1.0) / (c1 * (cuspLC[0] - 1.0) + cuspLC[1] * (l0 - l1))
            # Then one step Halley's method
            dL = l1 - l0
            dC = c1

            k_l = +0.3963377774 * a + 0.2158037573 * b
            k_m = -0.1055613458 * a - 0.0638541728 * b
            k_s = -0.0894841775 * a - 1.2914855480 * b

            l_dt = dL + dC * k_l
            m_dt = dL + dC * k_m
            s_dt = dL + dC * k_s

            # If higher accuracy is required, 2 or 3 iterations of the following block can be used:
            l = l0 * (1.0 - t) + t * l1
            c = t * c1

            l_ = l + c * k_l
            m_ = l + c * k_m
            s_ = l + c * k_s

            l = l_ * l_ * l_
            m = m_ * m_ * m_
            s = s_ * s_ * s_

            ldt = 3 * l_dt * l_ * l_
            mdt = 3 * m_dt * m_ * m_
            sdt = 3 * s_dt * s_ * s_

            ldt2 = 6 * l_dt * l_dt * l_
            mdt2 = 6 * m_dt * m_dt * m_
            sdt2 = 6 * s_dt * s_dt * s_

            r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s - 1
            r1 = 4.0767416621 * ldt - 3.3077115913 * mdt + 0.2309699292 * sdt
            r2 = 4.0767416621 * ldt2 - 3.3077115913 * mdt2 + 0.2309699292 * sdt2

            u_r = r1 / (r1 * r1 - 0.5 * r * r2)
            t_r = -r * u_r

            g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s - 1
            g1 = -1.2684380046 * ldt + 2.6097574011 * mdt - 0.3413193965 * sdt
            g2 = -1.2684380046 * ldt2 + 2.6097574011 * mdt2 - 0.3413193965 * sdt2

            u_g = g1 / (g1 * g1 - 0.5 * g * g2)
            t_g = -g * u_g

            b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s - 1
            b1 = -0.0041960863 * ldt - 0.7034186147 * mdt + 1.7076147010 * sdt
            b2 = -0.0041960863 * ldt2 - 0.7034186147 * mdt2 + 1.7076147010 * sdt2

            u_b = b1 / (b1 * b1 - 0.5 * b * b2)
            t_b = -b * u_b

            t_r = t_r if u_r >= 0.0 else sys.float_info.max
            t_g = t_g if u_g >= 0.0 else sys.float_info.max
            t_b = t_b if u_b >= 0.0 else sys.float_info.max

            t += min(t_r, t_g, t_b)
        
        return t
    
    @staticmethod
    def cuspToST(cuspLC: tuple):
        l: float = cuspLC[0]
        c: float = cuspLC[1]
        return (c / l, c / (1 - l))
    
    # Returns a smooth approximation of the location of the cusp
    # This polynomial was created by an optimization process
    # It has been designed so that S_mid < S_max and T_mid < T_max
    @staticmethod
    def getMidST(a_: float, b_: float):
        s = 0.11516993 + 1.0 / (+7.44778970 + 4.15901240 * b_
            + a_ * (-2.19557347 + 1.75198401 * b_
                + a_ * (-2.13704948 - 10.02301043 * b_
                    + a_ * (-4.24894561 + 5.38770819 * b_ + 4.69891013 * a_
                        ))))
        t = 0.11239642 + 1.0 / (+1.61320320 - 0.68124379 * b_
		    + a_ * (+0.40370612 + 0.90148123 * b_
			    + a_ * (-0.27087943 + 0.61223990 * b_
				    + a_ * (+0.00299215 - 0.45399568 * b_ - 0.14661872 * a_
					    ))))
        return (s, t)

    @staticmethod
    def getCs(l: float, a_: float, b_: float):
        cuspLC = Convert.findCuspLC(a_, b_)
        cMax = Convert.findGamutIntersection(a_, b_, l, 1, l, cuspLC)
        maxST = Convert.cuspToST(cuspLC)
        # Scale factor to compensate for the curved part of gamut shape:
        k = cMax / min(l * maxST[0], (1 - l) * maxST[1])
        midST = Convert.getMidST(a_, b_)
        # Use a soft minimum function, 
        # instead of a sharp triangle shape to get a smooth value for chroma.
        cMid = 0.9 * k * (1 / (1 / (l * midST[0]) ** 4 + 1 / ((1 - l) * midST[1]) ** 4)) ** (1 / 4)
        # for C_0, the shape is independent of hue, so ST are constant. 
        # Values picked to roughly be the average values of ST.
        c0 = (1 / (1 / (l * 0.4) ** 2 + 1 / ((1 - l) * 0.8) ** 2)) ** (1 / 2)
        return (c0, cMid, cMax)
    
    @staticmethod
    def rgbToTRC(rgb: tuple, trc: str):
        if trc == "sRGB":
            r = Convert.clampF(Convert.componentToSRGB(rgb[0]))
            g = Convert.clampF(Convert.componentToSRGB(rgb[1]))
            b = Convert.clampF(Convert.componentToSRGB(rgb[2]))
            return (r, g, b)
        else:
            r = Convert.componentToLinear(rgb[0])
            g = Convert.componentToLinear(rgb[1])
            b = Convert.componentToLinear(rgb[2])
            return (r, g, b)
    
    @staticmethod
    def rgbFToInt8(r: float, g: float, b: float, trc: str):
        if trc == "sRGB":
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
        else:
            r = round(Convert.componentToSRGB(r) * 255)
            g = round(Convert.componentToSRGB(g) * 255)
            b = round(Convert.componentToSRGB(b) * 255)
        return (r, g, b)
    
    @staticmethod
    def rgbFToHexS(r: float, g: float, b: float, trc: str):
        # hex codes are in 8 bits per color
        rgb = Convert.rgbFToInt8(r, g, b, trc)
        # hex converts int to str with first 2 char being 0x
        r = hex(rgb[0])[2:].zfill(2).upper()
        g = hex(rgb[1])[2:].zfill(2).upper()
        b = hex(rgb[2])[2:].zfill(2).upper()
        return f"#{r}{g}{b}"
    
    @staticmethod
    def hexSToRgbF(syntax: str, trc: str):
        if not syntax.startswith("#") or not (len(syntax) == 4 or len(syntax) == 7):
            return None
        try:
            r = int(syntax[1] + syntax[1] if len(syntax) == 4 else syntax[1:3], 16) / 255.0
            g = int(syntax[2] + syntax[2] if len(syntax) == 4 else syntax[3:5], 16) / 255.0
            b = int(syntax[3] + syntax[3] if len(syntax) == 4 else syntax[5:7], 16) / 255.0
        except ValueError:
            return None
        
        if trc == "sRGB":
            return (r, g, b)
        r = Convert.componentToLinear(r)
        g = Convert.componentToLinear(g)
        b = Convert.componentToLinear(b)
        return (r, g, b)
    
    @staticmethod
    def rgbFToOklabS(r: float, g: float, b: float, trc: str):
        # if rgb not linear, convert to linear for oklab conversion
        if trc == "sRGB":
            r = Convert.componentToLinear(r)
            g = Convert.componentToLinear(g)
            b = Convert.componentToLinear(b)
        oklab = Convert.linearToOklab(r, g, b)
        # l in percentage, a and b is 0 to 0.3+
        okL = round(oklab[0] * 100, 2)
        okA = Convert.roundZero(oklab[1], 4)
        okB = Convert.roundZero(oklab[2], 4)
        return f"oklab({okL}% {okA} {okB})"
    
    @staticmethod
    def oklabSToRgbF(syntax: str, trc: str):
        if not syntax.startswith("oklab"):
            return None
        strings = syntax[5:].strip("( )").split()
        if len(strings) != 3:
            return None
        okL = strings[0]
        okA = strings[1]
        okB = strings[2]
        try:
            if okL.endswith("%"):
                okL = Convert.clampF(float(okL[:-1]) / 100)
            else:
                okL = Convert.clampF(float(okL))
            if okA.endswith("%"):
                okA = Convert.clampF(float(okA[:-1]) / 250, 0.4, -0.4)
            else:
                okA = Convert.clampF(float(okA), 0.4, -0.4)
            if okB.endswith("%"):
                okB = Convert.clampF(float(okB[:-1]) / 250, 0.4, -0.4)
            else:
                okB = Convert.clampF(float(okB), 0.4, -0.4)
        except ValueError:
            return None
        rgb = Convert.oklabToLinear(okL, okA, okB)
        # if rgb not linear, perform transfer functions for components
        r = Convert.componentToSRGB(rgb[0]) if trc == "sRGB" else rgb[0]
        g = Convert.componentToSRGB(rgb[1]) if trc == "sRGB" else rgb[1]
        b = Convert.componentToSRGB(rgb[2]) if trc == "sRGB" else rgb[2]
        return (Convert.clampF(r), Convert.clampF(g), Convert.clampF(b))
    
    @staticmethod
    def rgbFToOklch(r: float, g: float, b: float, h: float, trc: str):
        # if rgb not linear, convert to linear for oklab conversion
        if trc == "sRGB":
            r = Convert.componentToLinear(r)
            g = Convert.componentToLinear(g)
            b = Convert.componentToLinear(b)
        oklab = Convert.linearToOklab(r, g, b)
        l = oklab[0]
        ch = Convert.cartesianToPolar(oklab[1], oklab[2])
        c = ch[0]
        # chroma of neutral colors will not be exactly 0 due to floating point errors
        if c < 0.000001:
            # use current hue to calulate chroma limit in sRGB gamut for neutral colors
            ab = Convert.polarToCartesian(1, h)
            u = Convert.findGamutIntersection(*ab, l, 1, l)
            c = 0
        else:
            # a and b must be normalized to c = 1 to calculate chroma limit in sRGB gamut
            a_ = oklab[1] / c
            b_ = oklab[2] / c
            u = Convert.findGamutIntersection(a_, b_, l, 1, l)
            if c > u:
                c = u
            # chroma adjustment due to rounding up blue hue
            if 264.052 < ch[1] < 264.06:
                h = 264.06
                c = round(c - 0.0001, 4)
            else:
                h = round(ch[1], 2)
                c = Convert.roundZero(c, 4)
        u = round(u - 0.0001, 4) if h == 264.06 else Convert.roundZero(u, 4)
        return (round(l * 100, 2), c, h, u)
    
    @staticmethod
    def oklchToRgbF(l: float, c: float, h: float, u: float, trc: str):
        l = l / 100
        # clip chroma if exceed sRGB gamut
        ab = Convert.polarToCartesian(1, h)
        if c:
            cMax = Convert.findGamutIntersection(*ab, l, 1, l)
            if u == -1:
                if c > cMax:
                    c = cMax
            else:
                s = (c + 0.00005) / (u + 0.00005)
                c = s * cMax
        rgb = Convert.oklabToLinear(l, ab[0] * c, ab[1] * c)
        # if rgb not linear, perform transfer functions for components
        r = Convert.componentToSRGB(rgb[0]) if trc == "sRGB" else rgb[0]
        g = Convert.componentToSRGB(rgb[1]) if trc == "sRGB" else rgb[1]
        b = Convert.componentToSRGB(rgb[2]) if trc == "sRGB" else rgb[2]
        return (Convert.clampF(r), Convert.clampF(g), Convert.clampF(b))
    
    @staticmethod
    def angleStoDeg(a: str):
        try:
            if a.endswith("deg"):
                d = float(a[:-3])
            elif a.endswith("grad"):
                d = (float(a[:-4]) / 10) * 9
            elif a.endswith("rad"):
                d = math.degrees(float(a[:-3]))
            elif a.endswith("turn"):
                d = float(a[:-4]) * 360
            else:
                d = float(a)
            return (d % 360) + 360 if d < 0 else d
        except ValueError:
            return None
    
    @staticmethod
    def rgbFToOklchS(r: float, g: float, b: float, trc: str):
        l, c, h, _ = Convert.rgbFToOklch(r, g, b, 0, trc)
        # l in percentage, c is 0 to 0.3+, h in degrees
        return f"oklch({l}% {c} {h})"
    
    @staticmethod
    def oklchSToRgbF(syntax: str, trc: str):
        if not syntax.startswith("oklch"):
            return None
        strings = syntax[5:].strip("( )").split()
        if len(strings) != 3:
            return None
        l = strings[0]
        c = strings[1]
        h = strings[2]
        try:
            if l.endswith("%"):
                l = Convert.clampF(float(l[:-1]) / 100)
            else:
                l = Convert.clampF(float(l))
            if c.endswith("%"):
                c = Convert.clampF(float(c[:-1]) / 250, 0.4)
            else:
                c = Convert.clampF(float(c), 0.4)
            h = Convert.angleStoDeg(h)
            if h is None:
                return None
        except ValueError:
            return None
        
        return Convert.oklchToRgbF(l * 100, c, h, -1, trc)
    
    @staticmethod
    def parseAnything(syntax: str, trc: str, curNotation: str):
        attempt = []
        
        if len(syntax) == 3 or len(syntax) == 6:
            attempt.append((Convert.hexSToRgbF, "#" + syntax, NOTATION[0]))
        if (len(syntax) == 4 or len(syntax) == 7) and syntax[0] == "#":
            attempt.append((Convert.hexSToRgbF, syntax, NOTATION[0]))
        
        if syntax.startswith("oklab"):
            attempt.append((Convert.oklabSToRgbF, syntax, NOTATION[1]))
        if syntax.startswith("oklch"):
            attempt.append((Convert.oklchSToRgbF, syntax, NOTATION[2]))
        if curNotation == NOTATION[1]:
            attempt.append((Convert.oklabSToRgbF, syntax, NOTATION[1]))
        if curNotation == NOTATION[2]:
            attempt.append((Convert.oklchSToRgbF, syntax, NOTATION[2]))
        
        components = syntax.split()
        if len(components) == 3:
            if curNotation == NOTATION[1] or components[1][0] == "-":
                attempt.append((Convert.oklabSToRgbF, f"oklab({components[0]} {components[1]} {components[2]})", NOTATION[1]))
            if curNotation == NOTATION[2] or components[2].endswith(("deg", "grad", "rad", "turn")):
                attempt.append((Convert.oklchSToRgbF, f"oklch({components[0]} {components[1]} {components[2]})", NOTATION[2]))

        for fn, val, notation in attempt:
            res = fn(val, trc)
            if res:
                return res, notation
        
        return None
    
    @staticmethod
    def hSectorToRgbF(hSector: float, v: float, m: float, x: float, trc: str="sRGB"):
        # assign max, med and min according to hue sector
        if hSector == 1: # between yellow and green
            r = x
            g = v
            b = m
        elif hSector == 2: # between green and cyan
            r = m
            g = v
            b = x
        elif hSector == 3: # between cyan and blue
            r = m
            g = x
            b = v
        elif hSector == 4: # between blue and magenta
            r = x
            g = m
            b = v
        elif hSector == 5: # between magenta and red
            r = v
            g = m
            b = x
        else: # between red and yellow
            r = v
            g = x
            b = m
        # convert to linear if not sRGB
        if trc == "sRGB":
            return (r, g, b)
        r = Convert.componentToLinear(r)
        g = Convert.componentToLinear(g)
        b = Convert.componentToLinear(b)
        return (r, g, b)

    @staticmethod
    def rgbFToHsv(r: float, g: float, b: float, trc: str):
        # if rgb is linear, convert to sRGB
        if trc == "linear":
            r = Convert.componentToSRGB(r)
            g = Convert.componentToSRGB(g)
            b = Convert.componentToSRGB(b)
        # value is equal to max(R,G,B) while min(R,G,B) determines saturation
        v = max(r,g,b)
        m = min(r,g,b)
        # chroma is the colorfulness of the color compared to the neutral color of equal value
        c = v - m
        if c == 0:
            # hue cannot be determined if the color is neutral
            return (0, 0, round(v * 100, 2))
        # hue is defined in 60deg sectors
        # hue = primary hue + deviation
        # max(R,G,B) determines primary hue while med(R,G,B) determines deviation
        # deviation has a range of -0.999... to 0.999...
        if v == r:
            # red is 0, range of hues that are predominantly red is -0.999... to 0.999... 
            # dividing (g - b) by chroma takes saturation and value out of the equation
            # resulting in hue deviation of the primary color
            h = ((g - b) / c) % 6
        elif v == g:
            # green is 2, range of hues that are predominantly green is 1.000... to 2.999...
            h = (b - r) / c + 2
        elif v == b:
            # blue is 4, range of hues that are predominantly blue is 3.000... to 4.999...
            h = (r - g) / c + 4
        # saturation is the ratio of chroma of the color to the maximum chroma of equal value
        # which is normalized chroma to fit the range of 0-1
        s = c / v
        return (round(h * 60, 2), round(s * 100, 2), round(v * 100, 2))

    @staticmethod
    def hsvToRgbF(h: float, s: float, v: float, trc: str):
        # derive hue in 60deg sectors
        h /= 60
        hSector = int(h)
        # scale saturation and value range from 0-100 to 0-1
        s /= 100
        v /= 100
        # max(R,G,B) = value
        # chroma = saturation * value
        # min(R,G,B) = max(R,G,B) - chroma
        m = v * (1 - s)
        # calculate deviation from closest secondary color with range of -0.999... to 0.999...
        # |deviation| = 1 - derived hue - hue sector if deviation is positive
        # |deviation| = derived hue - hue sector if deviation is negative
        d = h - hSector if hSector % 2 else 1 - (h - hSector)
        # med(R,G,B) = max(R,G,B) - (|deviation| * chroma)
        x = v * (1 - d * s)
        return Convert.hSectorToRgbF(hSector, v, m, x, trc)
    
    @staticmethod
    def rgbFToHsl(r: float, g: float, b: float, trc: str):
        # if rgb is linear, convert to sRGB
        if trc == "linear":
            r = Convert.componentToSRGB(r)
            g = Convert.componentToSRGB(g)
            b = Convert.componentToSRGB(b)
        v = max(r,g,b)
        m = min(r,g,b)
        # lightness is defined as the midrange of the RGB components
        l = (v + m) / 2
        c = v - m
        # hue cannot be determined if the color is neutral
        if c == 0:
            return (0, 0, round(l * 100, 2))
        # same formula as hsv to find hue
        if v == r:
            h = ((g - b) / c) % 6
        elif v == g:
            h = (b - r) / c + 2
        elif v == b:
            h = (r - g) / c + 4
        # saturation = chroma / chroma range
        # max chroma range when lightness at half
        s = c / (1 - abs(2 * l - 1))
        return (round(h * 60, 2), round(s * 100, 2), round(l * 100, 2))
    
    @staticmethod
    def hslToRgbF(h: float, s: float, l: float, trc: str):
        # derive hue in 60deg sectors
        h /= 60
        hSector = int(h)
        # scale saturation and value range from 0-100 to 0-1
        s /= 100
        l /= 100
        # max(R,G,B) = s(l) + l if l<0.5 else s(1 - l) + l
        v = l * (1 + s) if l < 0.5 else s * (1 - l) + l
        m = 2 * l - v
        # calculate deviation from closest secondary color with range of -0.999... to 0.999...
        d = h - hSector if hSector % 2 else 1 - (h - hSector)
        x = v - d * (v - m)
        return Convert.hSectorToRgbF(hSector, v, m, x, trc)
        
    @staticmethod
    def rgbFToHcy(r: float, g: float, b: float, h: float, trc: str, luma: bool):
        # if y should always be luma, convert to sRGB
        if luma and trc == "linear":
            r = Convert.componentToSRGB(r)
            g = Convert.componentToSRGB(g)
            b = Convert.componentToSRGB(b)
        # y can be luma or relative luminance depending on rgb format
        y = Y709R * r + Y709G * g + Y709B * b
        v = max(r, g, b)
        m = min(r, g, b)
        c = v - m
        yHue = 0
        # if color is neutral, use previous hue to calculate luma coefficient of hue
        # max(R,G,B) coefficent + med(R,G,B) coefficient * deviation from max(R,G,B) hue
        if (c != 0 and v == g) or (c == 0 and 60 <= h <= 180):
            h = (b - r) / c + 2 if c != 0 else h / 60
            if 1 <= h <= 2: # between yellow and green
                d = h - 1
                # luma coefficient of hue ranges from 0.9278 to 0.7152
                yHue = Y709G + Y709R * (1 - d)
            elif 2 < h <= 3: # between green and cyan
                d = h - 2
                # luma coefficient of hue ranges from 0.7152 to 0.7874
                yHue = Y709G + Y709B * d
        elif (c != 0 and v == b) or (c == 0 and 180 < h <= 300):
            h = (r - g) / c + 4 if c != 0 else h / 60
            if 3 < h <= 4: # between cyan and blue
                d = h - 3
                # luma coefficient of hue ranges from 0.7874 to 0.0722
                yHue = Y709B + Y709G * (1 - d)
            elif 4 < h <= 5: # between blue and magenta
                d = h - 4
                # luma coefficient of hue ranges from 0.0722 to 0.2848
                yHue = Y709B + Y709R * d
        elif (c != 0 and v == r) or (c == 0 and (h > 300 or h < 60)):
            h = ((g - b) / c) % 6 if c != 0 else h / 60
            if 5 < h <= 6: # between magenta and red
                d = h - 5
                # luma coefficient of hue ranges from 0.2848 to 0.2126
                yHue = Y709R + Y709B * (1 - d)
            elif 0 <= h < 1: # between red and yellow
                d = h
                # luma coefficient of hue ranges from 0.2126 to 0.9278
                yHue = Y709R + Y709G * d
        # calculate upper limit of chroma for hue and luma pair
        u = y / yHue if y <= yHue else (1 - y) / (1 - yHue)
        return (round(h * 60, 2), round(c * 100, 3), round(y * 100, 2), round(u * 100, 3))
    
    @staticmethod
    def hcyToRgbF(h: float, c: float, y: float, u: float, trc: str, luma: bool):
        # derive hue in 60deg sectors
        h /= 60
        hSector = int(h)
        # pass in y and u as -1 for max chroma conversions
        if y != -1:
            # scale luma to 1
            y /= 100
        if c == 0 or y == 0 or y == 1:
            # if y is always luma, convert to linear
            if luma and trc == "linear":
                y = Convert.componentToLinear(y)
            # luma coefficients add up to 1
            return (y, y, y)
        # calculate deviation from closest primary color with range of -0.999... to 0.999...
        # |deviation| = 1 - derived hue - hue sector if deviation is negative
        # |deviation| = derived hue - hue sector if deviation is positive
        d = h - hSector if hSector % 2 == 0 else 1 - (h - hSector)
        # calculate luma coefficient of hue
        yHue = 0
        if hSector == 1: # between yellow and green
            yHue = Y709G + Y709R * d
        elif hSector == 2: # between green and cyan
            yHue = Y709G + Y709B * d
        elif hSector == 3: # between cyan and blue
            yHue = Y709B + Y709G * d
        elif hSector == 4: # between blue and magenta
            yHue = Y709B + Y709R * d
        elif hSector == 5: # between magenta and red
            yHue = Y709R + Y709B * d
        else: # between red and yellow
            yHue = Y709R + Y709G * d
        # when chroma is at maximum, y = luma coefficient of hue
        if y == -1:
            y = yHue
        # it is not always possible for chroma to be constant when adjusting hue or luma
        # adjustment have to either clip chroma or have consistent saturation instead
        cMax = y / yHue if y <= yHue else (1 - y) / (1 - yHue)
        if u == -1:
            # scale chroma to 1 before comparing
            c /= 100
            # clip chroma to new limit
            if c > cMax:
                c = cMax
        else:
            # scale chroma to hue or luma adjustment
            s = 0
            if u:
                s = c / u
            c = s * cMax
        # luma = max(R,G,B) * yHue + min(R,G,B) * (1 - yHue)
        # calculate min(R,G,B) based on the equation above
        m = y - c * yHue
        # med(R,G,B) = min(R,G,B) + (|deviation| * chroma)
        x = y - c * (yHue - d)
        # max(R,G,B) = min(R,G,B) + chroma
        v = y + c * (1 - yHue)
        # if y is always luma, hsector to rgbf needs trc param
        if luma:
            return Convert.hSectorToRgbF(hSector, v, m, x, trc)
        return Convert.hSectorToRgbF(hSector, v, m, x)
    
    @staticmethod
    def rgbFToOkhcl(r: float, g: float, b: float, h: float, trc: str):
        # if rgb not linear, convert to linear for oklab conversion
        if trc == "sRGB":
            r = Convert.componentToLinear(r)
            g = Convert.componentToLinear(g)
            b = Convert.componentToLinear(b)
        oklab = Convert.linearToOklab(r, g, b)
        l = oklab[0]
        ch = Convert.cartesianToPolar(oklab[1], oklab[2])
        c = ch[0]
        # chroma of neutral colors will not be exactly 0 due to floating point errors
        if c < 0.000001:
            # use current hue to calulate chroma limit in sRGB gamut for neutral colors
            ab = Convert.polarToCartesian(1, h)
            cuspLC = Convert.findCuspLC(*ab)
            u = Convert.findGamutIntersection(*ab, l, 1, l, cuspLC)
            u /= cuspLC[1]
            c = 0
        else:
            # gamut intersection jumps for parts of blue
            h = ch[1] if not 264.052 < ch[1] < 264.06 else 264.06
            # a and b must be normalized to c = 1 to calculate chroma limit in sRGB gamut
            a_ = oklab[1] / c
            b_ = oklab[2] / c
            cuspLC = Convert.findCuspLC(a_, b_)
            u = Convert.findGamutIntersection(a_, b_, l, 1, l, cuspLC)
            if c > u:
                c = u
            u /= cuspLC[1]
            c /= cuspLC[1]
        l = Convert.toe(l)
        return (round(h, 2), round(c * 100, 3), round(l * 100, 2), round(u * 100, 3))
    
    @staticmethod
    def okhclToRgbF(h: float, c: float, l: float, u: float, trc: str):
        # convert lref back to okL
        l = Convert.toeInv(l / 100)
        # clip chroma if exceed sRGB gamut
        ab = Convert.polarToCartesian(1, h)
        if c:
            cuspLC = Convert.findCuspLC(*ab)
            cMax = Convert.findGamutIntersection(*ab, l, 1, l, cuspLC)
            if u == -1:
                c = c / 100 * cuspLC[1]
                if c > cMax:
                    c = cMax
            else:
                s = c / u
                c = s * cMax
        rgb = Convert.oklabToLinear(l, ab[0] * c, ab[1] * c)
        # perform transfer functions for components if output to sRGB
        r = Convert.componentToSRGB(rgb[0]) if trc == "sRGB" else rgb[0]
        g = Convert.componentToSRGB(rgb[1]) if trc == "sRGB" else rgb[1]
        b = Convert.componentToSRGB(rgb[2]) if trc == "sRGB" else rgb[2]
        return (Convert.clampF(r), Convert.clampF(g), Convert.clampF(b))
    
    @staticmethod
    def rgbFToOkhsv(r: float, g: float, b: float, trc: str):
        # if rgb not linear, convert to linear for oklab conversion
        if trc == "sRGB":
            r = Convert.componentToLinear(r)
            g = Convert.componentToLinear(g)
            b = Convert.componentToLinear(b)
        oklab = Convert.linearToOklab(r, g, b)
        l = oklab[0]
        ch = Convert.cartesianToPolar(oklab[1], oklab[2])
        c = ch[0]
        # chroma of neutral colors will not be exactly 0 due to floating point errors
        if c < 0.000001:
            return (0, 0, round(Convert.toe(l) * 100, 2))
        else:
            # gamut intersection jumps for parts of blue
            h = ch[1] if not 264.052 < ch[1] < 264.06 else 264.06
            # a and b must be normalized to c = 1 to calculate chroma limit in sRGB gamut
            a_ = oklab[1] / c
            b_ = oklab[2] / c
            cuspLC = Convert.findCuspLC(a_, b_)
            st = Convert.cuspToST(cuspLC)
            sMax = st[0]
            tMax = st[1]
            s0 = 0.5
            k = 1 - s0 / sMax
            # first we find L_v, C_v, L_vt and C_vt
            t = tMax / (c + l * tMax)
            l_v = t * l
            c_v = t * c
            l_vt = Convert.toeInv(l_v)
            c_vt = c_v * l_vt / l_v
            # we can then use these to invert the step that compensates for the toe 
            # and the curved top part of the triangle:
            rgbScale = Convert.oklabToLinear(l_vt, a_ * c_vt, b_ * c_vt)
            scaleL = (1 / max(rgbScale[0], rgbScale[1], rgbScale[2])) ** (1 / 3)
            l = Convert.toe(l / scaleL)
            # // we can now compute v and s:
            v = l / l_v
            s = (s0 + tMax) * c_v / ((tMax * s0) + tMax * k * c_v)
            if s > 1:
                s = 1.0
            return (round(h, 2), round(s * 100, 2), round(v * 100, 2))
        
    @staticmethod
    def okhsvToRgbF(h: float, s: float, v: float, trc: str):
        # scale saturation and value range from 0-100 to 0-1
        s /= 100
        v /= 100
        rgb = None
        if v == 0:
            return (0, 0, 0)
        elif s == 0:
            rgb = Convert.oklabToLinear(Convert.toeInv(v), 0, 0)
        else:
            ab = Convert.polarToCartesian(1, h)
            cuspLC = Convert.findCuspLC(*ab)
            st = Convert.cuspToST(cuspLC)
            sMax = st[0]
            tMax = st[1]
            s0 = 0.5
            k = 1 - s0 / sMax
            # first we compute L and V as if the gamut is a perfect triangle:
            # L, C when v==1:
            l_v = 1 - s * s0 / (s0 + tMax - tMax * k * s)
            c_v = s * tMax * s0 / (s0 + tMax - tMax * k * s)
            l = v * l_v
            c = v * c_v
            # then we compensate for both toe and the curved top part of the triangle:
            l_vt = Convert.toeInv(l_v)
            c_vt = c_v * l_vt / l_v
            l_new = Convert.toeInv(l)
            c *= l_new / l
            l = l_new
            rgbScale = Convert.oklabToLinear(l_vt, ab[0] * c_vt, ab[1] * c_vt)
            scaleL = (1 / max(rgbScale[0], rgbScale[1], rgbScale[2])) ** (1 / 3)
            l *= scaleL
            c *= scaleL
            rgb = Convert.oklabToLinear(l, ab[0] * c, ab[1] * c)
        # perform transfer functions for components if output to sRGB
        r = Convert.componentToSRGB(rgb[0]) if trc == "sRGB" else rgb[0]
        g = Convert.componentToSRGB(rgb[1]) if trc == "sRGB" else rgb[1]
        b = Convert.componentToSRGB(rgb[2]) if trc == "sRGB" else rgb[2]
        return (Convert.clampF(r), Convert.clampF(g), Convert.clampF(b))
    
    @staticmethod
    def rgbFToOkhsl(r: float, g: float, b: float, trc: str):
        # if rgb not linear, convert to linear for oklab conversion
        if trc == "sRGB":
            r = Convert.componentToLinear(r)
            g = Convert.componentToLinear(g)
            b = Convert.componentToLinear(b)
        oklab = Convert.linearToOklab(r, g, b)
        l = oklab[0]
        ch = Convert.cartesianToPolar(oklab[1], oklab[2])
        s = 0
        c = ch[0]
        # chroma of neutral colors will not be exactly 0 due to floating point errors
        if c >= 0.000001:
            a_ = oklab[1] / c
            b_ = oklab[2] / c
            cs = Convert.getCs(l, a_, b_)
            c0 = cs[0]
            cMid = cs[1]
            cMax = cs[2]
            # Inverse of the interpolation in okhsl_to_srgb:
            mid = 0.8
            midInv = 1.25
            if c < cMid:
                k1 = mid * c0
                k2 = 1 - k1 / cMid
                t = c / (k1 + k2 * c)
                s = t * mid
            else:
                k1 = (1 - mid) * cMid * cMid * midInv * midInv / c0
                k2 = 1 - k1 / (cMax - cMid)
                t = (c - cMid) / (k1 + k2 * (c - cMid))
                s = mid + (1 - mid) * t
        # gamut intersection jumps for parts of blue
        h = ch[1] if not 264.052 < ch[1] < 264.06 else 264.06
        l = Convert.toe(l)
        return (round(h, 2), round(s * 100, 2), round(l * 100, 2))

    @staticmethod
    def okhslToRgbF(h: float, s: float, l: float, trc: str):
        # scale saturation and lightness range from 0-100 to 0-1
        s /= 100
        l /= 100
        if l == 0 or l == 1:
            return (l, l, l)
        ab = Convert.polarToCartesian(1, h)
        l = Convert.toeInv(l)
        c = 0
        if s:
            cs = Convert.getCs(l, *ab)
            c0 = cs[0]
            cMid = cs[1]
            cMax = cs[2]
            # Interpolate the three values for C so that:
            # At s=0: dC/ds = C_0, C=0
            # At s=0.8: C=C_mid
            # At s=1.0: C=C_max
            mid = 0.8
            midInv = 1.25
            if s < mid:
                t = midInv * s
                k1 = mid * c0
                k2 = 1 - k1 / cMid
                c = t * k1 / (1 - k2 * t)
            else:
                t = (s - mid) / (1 - mid)
                k1 = (1 - mid) * cMid * cMid * midInv * midInv / c0
                k2 = 1 - k1 / (cMax - cMid)
                c = cMid + t * k1 / (1 - k2 * t)
        rgb = Convert.oklabToLinear(l, ab[0] * c, ab[1] * c)
        # perform transfer functions for components if output to sRGB
        r = Convert.componentToSRGB(rgb[0]) if trc == "sRGB" else rgb[0]
        g = Convert.componentToSRGB(rgb[1]) if trc == "sRGB" else rgb[1]
        b = Convert.componentToSRGB(rgb[2]) if trc == "sRGB" else rgb[2]
        return (Convert.clampF(r), Convert.clampF(g), Convert.clampF(b))
    
