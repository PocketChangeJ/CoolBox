import matplotlib.pyplot as plt
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
from mpl_toolkits.axes_grid1.colorbar import colorbar

import numpy as np
from scipy import ndimage

from coolbox.utilities import (
    GenomeRange,
    change_chrom_names,
    get_logger
)

from coolbox.plots.track.base import TrackPlot
from coolbox.utilities import shiftedColorMap

from . import cool
PlotCool = cool.PlotCool


log = get_logger(__name__)


class PlotHicCompare(TrackPlot):

    DEFAULT_COLOR = 'bwr'

    def __init__(self, *args, **kwargs):
        TrackPlot.__init__(self, *args, **kwargs)
        self.hic1 = self.properties['hic1']
        self.hic2 = self.properties['hic2']
        self.__set_default_properties()

    def __set_default_properties(self):
        self.properties['height'] = 'cool_auto'

        if 'color' not in self.properties:
            self.properties['color'] = PlotHicCompare.DEFAULT_COLOR
        self.properties['triangular'] = 'no'
        if 'color_bar' not in self.properties:
            self.properties['color_bar'] = 'yes'
        if 'transform' not in self.properties:
            self.properties['transform'] = 'no'
        if 'title' not in self.properties:
            self.properties['title'] = ''
        if 'norm' not in self.properties:
            self.properties['norm'] = 'log'
        self.properties['style'] = 'matrix'

    def plot(self, ax, chrom_region, start_region, end_region):
        self.ax = ax

        genome_range = GenomeRange(chrom_region, start_region, end_region)
        arr1 = self.hic1.__fetch_matrix(genome_range)
        self.hic1.matrix = arr1
        arr2 = self.hic2.__fetch_matrix(genome_range)
        self.hic2.matrix = arr2
        self.matrix = np.triu(arr1 * (-1), 1) + np.tril(arr2, -1)

        img = self.__plot_matrix(genome_range)
        self.__adjust_figure(genome_range)
        if self.properties['color_bar'] == 'yes':
            self.__plot_colorbar(img)
        else:
            pass
        self.plot_label()

    def __plot_matrix(self, genome_range):
        start, end = genome_range.start, genome_range.end
        ax = self.ax
        arr = self.matrix
        if isinstance(self.properties['color'], str):
            cmap = plt.get_cmap(self.properties['color'])
        else:
            cmap = self.properties['color']
        cmap.set_bad("white")
        cmap.set_under("white")
        c_min_1, c_max_1 = self.hic1.matrix_val_range
        c_min_2, c_max_2 = self.hic2.matrix_val_range

        self.small_value = ( abs(c_min_1) + abs(c_min_2) ) / 2

        if self.properties['norm'] == 'log':
            a_ = np.log10(c_max_1)
            b_ = np.log10(c_max_2)
            c_ = np.log10(self.small_value)
            ra_ = abs(c_ - a_) + 0.7
            rb_ = abs(c_ - b_) + 0.7

            midpoint = (ra_ / (ra_ + rb_))
        else:
            midpoint = (abs(c_max_2) / (abs(c_max_1) + abs(c_max_2)))

        cmap = shiftedColorMap(cmap, midpoint=midpoint)

        img = ax.matshow(arr, cmap=cmap,
                         extent=(start, end, end, start),
                         aspect='auto')

        if self.properties['norm'] == 'log':
            img.set_norm(colors.SymLogNorm(linthresh=self.small_value, linscale=1, vmin=-c_max_1, vmax=c_max_2))
        else:
            img.set_norm(colors.Normalize(vmin=-c_max_1, vmax=c_max_2))

        return img

    def __adjust_figure(self, genome_range):
        ax = self.ax
        start, end = genome_range.start, genome_range.end
        ax.set_ylim(end, start)
        ax.set_xlim(start, end)

    def __plot_colorbar(self, img):
        ax_divider = make_axes_locatable(self.ax)
        cax = ax_divider.append_axes("bottom", size=0.09, pad=0.2)
        plt.colorbar(img, cax=cax, orientation='horizontal')

    def get_tracks_height(self, frame_width):
        """
        calculate track height dynamically.
        """
        cool_height = frame_width
        cool_height *= 0.8
        if 'color_bar' in self.properties and self.properties['color_bar'] != 'no':
            cool_height += 1.5

        return cool_height
