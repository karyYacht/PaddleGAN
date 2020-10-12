import paddle
import functools
import numpy as np
import paddle.nn as nn
import paddle.nn.functional as F

from ...modules.nn import Conv2d, Spectralnorm
from ...modules.norm import build_norm_layer

from .builder import DISCRIMINATORS


@DISCRIMINATORS.register()
class NLayerDiscriminator(paddle.nn.Layer):
    """Defines a PatchGAN discriminator"""
    def __init__(self, input_nc, ndf=64, n_layers=3, norm_type='instance'):
        """Construct a PatchGAN discriminator

        Parameters:
            input_nc (int)  -- the number of channels in input images
            ndf (int)       -- the number of filters in the last conv layer
            n_layers (int)  -- the number of conv layers in the discriminator
            norm_layer      -- normalization layer
        """
        super(NLayerDiscriminator, self).__init__()
        norm_layer = build_norm_layer(norm_type)
        if type(
                norm_layer
        ) == functools.partial:  # no need to use bias as BatchNorm2d has affine parameters
            use_bias = norm_layer.func == nn.InstanceNorm2d
        else:
            use_bias = norm_layer == nn.InstanceNorm2d

        kw = 4
        padw = 1
        #sequence = [Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw), nn.LeakyReLU(0.01)]
        sequence = [
            Spectralnorm(
                Conv2d(input_nc, ndf, kernel_size=kw, stride=2, padding=padw)),
            nn.LeakyReLU(0.01)
        ]
        nf_mult = 1
        nf_mult_prev = 1
        for n in range(1, n_layers):  # gradually increase the number of filters
            nf_mult_prev = nf_mult
            nf_mult = min(2**n, 8)
            sequence += [
                #Conv2d(ndf * nf_mult_prev, ndf * nf_mult, kernel_size=kw, stride=2, padding=padw, bias_attr=use_bias),
                Spectralnorm(
                    Conv2d(ndf * nf_mult_prev,
                           ndf * nf_mult,
                           kernel_size=kw,
                           stride=2,
                           padding=padw)),
                #norm_layer(ndf * nf_mult),
                nn.LeakyReLU(0.01)
            ]

        nf_mult_prev = nf_mult
        nf_mult = min(2**n_layers, 8)
        sequence += [
            #Conv2d(ndf * nf_mult_prev, ndf * nf_mult, kernel_size=kw, stride=1, padding=padw, bias_attr=use_bias),
            Spectralnorm(
                Conv2d(ndf * nf_mult_prev,
                       ndf * nf_mult,
                       kernel_size=kw,
                       stride=1,
                       padding=padw)),
            #norm_layer(ndf * nf_mult),
            nn.LeakyReLU(0.01)
        ]

        #sequence += [Conv2d(ndf * nf_mult, 1, kernel_size=kw, stride=1, padding=padw)]  # output 1 channel prediction map
        sequence += [
            Spectralnorm(
                Conv2d(ndf * nf_mult,
                       1,
                       kernel_size=kw,
                       stride=1,
                       padding=padw,
                       bias_attr=False))
        ]  # output 1 channel prediction map
        self.model = nn.Sequential(*sequence)

    def forward(self, input):
        """Standard forward."""
        return self.model(input)
