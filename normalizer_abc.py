from __future__ import division

from abc import ABC, abstractmethod
import utils.misc_utils as mu
import spams
import numpy as np

class Normaliser(ABC):

    @abstractmethod
    def fit(self, target):
        """Fit the normalizer to an target image"""

    @abstractmethod
    def transform(self, I):
        """Transform an image to the target stain"""


class FancyNormalizer(Normaliser):

    @abstractmethod
    def get_stain_matrix(self, I, *args):
        """Estimate stain matrix given an image and relevant method parameters"""

    def target_stains(self):
        """
        Get target stains as RGB
        :return:
        """
        assert self.stain_matrix_target is not None, 'Run fit method first.'
        return mu.OD_to_RGB(self.stain_matrix_target)

    def hematoxylin(self, I):
        """
        Hematoxylin channel
        :param I:
        :return:
        """
        I = mu.standardize_brightness(I)
        h, w, c = I.shape
        stain_matrix_source = self.get_stain_matrix(I)
        source_concentrations = self.get_concentrations(I, stain_matrix_source)
        H = source_concentrations[:, 0].reshape(h, w)
        H = np.exp(-1 * H)
        return H

    @staticmethod
    def get_concentrations(I, stain_matrix, lamda=0.01):
        """
        Get the concentration matrix. Suppose the input image is H x W x 3 (uint8). Define Npix = H * W.
        Then the concentration matrix is Npix x 2 (or we could reshape to H x W x 2).
        The first element of each row is the Hematoxylin concentration.
        The second element of each row is the Eosin concentration.

        We do this by 'solving' OD = C*S (Matrix product) where OD is optical density (Npix x 3),\
        C is concentration (Npix x 2) and S is stain matrix (2 x 3).
        See docs for spams.lasso.

        We restrict the concentrations to be positive and penalise very large concentration values,\
        so that background pixels (which can not easily be expressed in the Hematoxylin-Eosin basis) have \
        low concentration and thus appear white.

        :param I: Image. A np array HxWx3 of type uint8.
        :param stain_matrix: a 2x3 stain matrix. First row is Hematoxylin stain vector, second row is Eosin stain vector.
        :return:
        """
        OD = mu.RGB_to_OD(I).reshape((-1, 3))  # convert to optical density and flatten to (H*W)x3.
        return spams.lasso(OD.T, D=stain_matrix.T, mode=2, lambda1=lamda, pos=True).toarray().T