# https://medium.com/analytics-vidhya/multivariate-linear-regression-from-scratch-using-ols-ordinary-least-square-estimator-859646708cd6
import numpy as np


class LinearRegressionLS:
    def __init__(self, fit_intercept=True):
        self.coef_ = None
        self.intercept_ = None
        self._bias = None
        self.pn = None
        self.fit_intercept = fit_intercept

    def _add_bias(self, x):
        if len(x.shape) == 1:
            x = x[:, np.newaxis]
        b = np.ones((x.shape[0], 1))
        x = np.concatenate((b, x), axis=1)
        return x

    def fit(self, X, y):
        """With this function we are calculate the weights"""
        if self.fit_intercept:
            X = X.copy()
            X = self._add_bias(X)

        first = np.dot(X.T, X)
        first.astype(np.float16)
        inverse = np.linalg.inv(first)
        self.pn = inverse
        second = np.dot(X.T, y)

        self._bias = np.dot(inverse, second).reshape(-1)
        self.intercept_ = self._bias[0]
        self.coef_ = self._bias[1:]
        return

    def update(self, X, y, lamda=1):
        """Need to update self.coef_, self.intercept_, self._bias
        based on new data points
        """
        if self.fit_intercept:
            X = X.copy()
            X = self._add_bias(X)

        w_old = self._bias
        pn = self.pn
        xt_p = np.dot(X, pn)
        xt_p_x = np.dot(xt_p, X.T)
        numerator = np.dot(pn, X.T)
        denominator = lamda + xt_p_x
        w_old_xt = np.dot(X, w_old)
        second_numerator = y.to_numpy().reshape(-1) - w_old_xt
        final_numerator = np.dot(numerator, second_numerator)
        new_weights = final_numerator / denominator
        w_new = w_old + new_weights

        # update intercept, coef
        self._bias = w_new[0]
        self.intercept_ = self._bias[0]
        self.coef_ = self._bias[1:]

        # update pn
        kn = numerator / denominator
        self.pn = (1 / lamda) * (pn - np.dot(np.dot(kn, X), pn))

        return

    def update_many(self, X, y):
        window_size = len(X)
        try:
            for i in range(0, window_size):
                self.update(X.iloc[[i], :], y.iloc[[i], :])
        except Exception:
            print("Error: ", i)

    def predict(self, X):
        if self.fit_intercept:
            X = X.copy()
            X = self._add_bias(X)

        return np.dot(X, self._bias)
