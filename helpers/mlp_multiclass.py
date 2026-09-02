# ============================================================
# Feedforward Neural Network
# Binary  -> multiclass = False
# Multiclass -> multiclass = True
# ============================================================

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score)

# ============================================================
# Activations and Derivatives
# ============================================================

def tanh(x):
    return np.tanh(x)

def d_tanh(x):
    return 1 - np.tanh(x)**2

def relu(x):
    return np.maximum(0, x)

def d_relu(x):
    return (x > 0).astype(float)

def softmax(x):
    x = x - np.max(x)
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x, axis=0, keepdims=True)

def d_softmax(x):
    s = softmax(x).reshape(-1, 1)
    return np.diagflat(s) - np.dot(s, s.T)

# ============================================================
# LOSSES
# ============================================================

def cross_entropy(y_true, y_pred):
    eps = 1e-12
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.sum(y_true * np.log(y_pred))

def one_hot(y, n_classes=None):
    y = np.array(y)
    if n_classes is None:
        n_classes = len(list(set(y)))
    out = np.zeros((len(y), n_classes))
    out[np.arange(len(y)), y] = 1
    return out

# He Initialization for relu
def He_(fan_in, fan_out):
    std = np.sqrt(2 / fan_in)
    return np.random.randn(fan_out, fan_in + 1) * std

# Xavier Initialization for tanh
def Xavier(fan_in, fan_out):
    limit = np.sqrt(6 / (fan_in + fan_out))
    return np.random.uniform(low=-limit, high=limit, size=(fan_out, fan_in + 1))

def normal(fan_in, fan_out):
    self.weights.append(np.random.uniform(low=-1.0, high=1.0, size=(fan_out, fan_in + 1)))

# ============================================================
# NEURON
# ============================================================

class Neuron:

    def __init__(self, act_func, d_act_func):
        self.activation_function = act_func
        self.activation_function_derivative = d_act_func
        self.pre_activation = 0
        self.post_activation = 0

    def process(self, v):
        self.pre_activation = v
        self.post_activation = self.activation_function(v)
        return self.post_activation

    def process_d(self):
        return self.activation_function_derivative(self.pre_activation)

# ============================================================
# LAYER
# ============================================================

class Layer:

    def __init__(
        self,
        dimension,
        neuron_model,
        act_func,
        d_act_func,
        multiclass=False
    ):

        self.dimension = dimension
        self.neurons = np.empty(dimension, dtype=object)
        self.pre_activation = np.zeros((dimension,1))
        self.post_activation = np.zeros((dimension,1))
        self.local_derivatives = np.zeros((dimension,1))
        self.multiclass = multiclass
        for i in range(dimension):
            self.neurons[i] = neuron_model(
                act_func,
                d_act_func
            )

    def process(self, v, learn=False):
        self.pre_activation = np.array(v).reshape(-1,1)
        # ====================================================
        # SOFTMAX
        # ====================================================
        if self.multiclass:
            output = self.neurons[0].activation_function(self.pre_activation)
            self.post_activation = output
            if learn:
                self.local_derivatives = np.ones_like(output)
            return output

        # ====================================================
        # NORMAL LAYER
        # ====================================================
        output = []
        deriv = []
        for i, neuron in enumerate(self.neurons):
            output.append(neuron.process(v[i]))
            if learn:
                deriv.append(neuron.process_d())
        self.post_activation = np.array(output).reshape(-1,1)
        if learn:
            self.local_derivatives = np.array(deriv).reshape(-1,1)
        return self.post_activation

# ============================================================
# FEEDFORWARD NETWORK
# ============================================================

class FFNeuralNetwork:
    def __init__(
        self,
        topology,
        layers,
        W0=None,
        zero_init=False,
        rand_seed=0,
        multiclass=False,
        method_init=None,
        lambda_l2=0.0
    ):
        self.topology = topology
        self.layers = layers
        self.n_layers = len(topology) - 1
        self.multiclass = multiclass
        self.weights = W0
        self.e_epochs = []
        self.loss_epochs = []
        self.lambda_l2 = lambda_l2

        if self.weights is None:
            self.weights = []
            np.random.seed(rand_seed)
            for i in range(len(topology)-1):
                fan_in = topology[i]
                fan_out = topology[i+1]
                if zero_init:
                    w = np.zeros((fan_out, fan_in + 1))
                else:
                    w = method_init(fan_in, fan_out)
                self.weights.append(w)

    # ========================================================
    # FORWARD
    # ========================================================

    def process(self, x, learn=False):
        for i, layer in enumerate(self.layers):
            if i == 0:
                x_in = np.vstack((x, [[1]]))
            else:
                x_in = np.vstack((self.layers[i-1].post_activation, [[1]]))
            v = self.weights[i] @ x_in
            layer.process(v, learn)
        return self.layers[-1].post_activation

    # ========================================================
    # BACKPROP
    # ========================================================

    def backprop(self, x, y_d, eta):
        output = self.process(x, learn=True)
        error_vector = y_d - output
        local_grads = [
            np.zeros((self.topology[i+1],1))
            for i in range(self.n_layers)
        ]
        for l_idx in reversed(range(self.n_layers)):
            # =================================================
            # OUTPUT LAYER
            # =================================================
            if l_idx == self.n_layers - 1:
                # MULTICLASS
                if self.multiclass:
                    delta_k = output - y_d
                # BINARY
                else:
                    delta_k = (error_vector * self.layers[-1].local_derivatives)
                local_grads[l_idx] = delta_k
            # =================================================
            # HIDDEN LAYERS
            # =================================================
            else:
                delta_k_1 = (
                    self.layers[l_idx].local_derivatives * (self.weights[l_idx+1][:,:-1].T @ local_grads[l_idx+1]))
                local_grads[l_idx] = delta_k_1
        # =====================================================
        # UPDATE WEIGHTS
        # =====================================================
        for i in range(self.n_layers):
            if i == 0:
                x_in = np.vstack((x, [[1]]))
            else:
                x_in = np.vstack((self.layers[i-1].post_activation, [[1]]))
        
            # =========================================
            # GRADIENTE NORMAL
            # =========================================
            grad = local_grads[i] @ x_in.T
            # =========================================
            # L2 REGULARIZATION
            # =========================================
            reg = self.lambda_l2 * self.weights[i]
            # NÃO regulariza bias
            reg[:, -1] = 0
            # =========================================
            # UPDATE
            # =========================================
            self.weights[i] = (self.weights[i] - eta * (grad + reg))

        return error_vector

    # ========================================================
    # TRAIN
    # ========================================================

    def fit(self, X, y, learning_rate=0.01, n_epochs=500):
        self.loss_epochs = []
        indices = np.arange(len(X))
        y = one_hot(y)
        for epoch in range(n_epochs):
            np.random.shuffle(indices)
            losses = []
            for k in indices:
                x_i = X[k].reshape(-1,1)
                # =============================================
                # MULTICLASS
                # =============================================
                if self.multiclass:
                    y_i = y[k].reshape(-1,1)
                # =============================================
                # BINARY
                # =============================================
                else:
                    y_i = np.array([[y[k]]])
                self.backprop(x_i, y_i, learning_rate)
                output = self.process(x_i)
                # =============================================
                # LOSS
                # =============================================
                if self.multiclass:
                    loss = cross_entropy(y_i, output)
                else:
                    loss = np.mean((y_i - output)**2)
                losses.append(loss)

            epoch_loss = np.mean(losses)
            self.loss_epochs.append(epoch_loss)
            if epoch % 50 == 0:
                print(f"Epoch {epoch} | Loss: {epoch_loss:.6f}")
        return self
    
    def fit_with_validation(self, X_train, y_train, X_val, y_val, learning_rate=0.01, n_epochs=500, patience=20, min_delta=1e-4):
        self.loss_epochs = []
        self.val_loss_epochs = []
        best_val_loss = np.inf
        best_weights = None
        patience_counter = 0
        indices = np.arange(len(X_train))
        y_train = one_hot(y_train)
        y_val = one_hot(y_val)
        for epoch in range(n_epochs):
            np.random.shuffle(indices)
            train_losses = []
            # ====================================================
            # TRAIN
            # ====================================================
            for k in indices:
                x_i = X_train[k].reshape(-1,1)
                if self.multiclass:
                    y_i = y_train[k].reshape(-1,1)
                else:
                    y_i = np.array([[y_train[k]]])
                self.backprop(x_i, y_i, learning_rate)
                output = self.process(x_i)
                if self.multiclass:
                    loss = cross_entropy(y_i, output)
                else:
                    loss = np.mean((y_i - output)**2)
                train_losses.append(loss)
            train_loss = np.mean(train_losses)
            self.loss_epochs.append(train_loss)
            # ====================================================
            # VALIDATION
            # ====================================================
            val_losses = []
            for i in range(len(X_val)):
                x_i = X_val[i].reshape(-1,1)
                if self.multiclass:
                    y_i = y_val[i].reshape(-1,1)
                else:
                    y_i = np.array([[y_val[i]]])
                output = self.process(x_i)
                if self.multiclass:
                    loss = cross_entropy(y_i, output)
                else:
                    loss = np.mean((y_i - output)**2)
                val_losses.append(loss)
            val_loss = np.mean(val_losses)
            self.val_loss_epochs.append(val_loss)
            # ============================================
            # EARLY STOPPING
            # ============================================
            if val_loss < (best_val_loss - min_delta):
                best_val_loss = val_loss
                best_weights = [w.copy() for w in self.weights]
                patience_counter = 0
            else:            
                patience_counter += 1
            # ============================================
            # STOP CONDITION
            # ============================================
            if patience_counter >= patience:
                print(f"\nEarly stopping at epoch {epoch}")
                print(f"Best validation loss: "f"{best_val_loss:.6f}")
                # restaura melhores pesos            
                self.weights = best_weights
                break
            # ====================================================
            # LOG
            # ====================================================
            if epoch % 50 == 0:
                print(
                    f"Epoch {epoch} | "
                    f"Train Loss: {train_loss:.6f} | "
                    f"Val Loss: {val_loss:.6f}"
                )
        return self

    # ========================================================
    # PREDICT
    # ========================================================
    def predict(self, X, threshold=0.5):
        y_probs = []
        y_preds = []
        for i in range(len(X)):
            x_i = X[i].reshape(-1,1)
            probs = self.process(x_i)
            # =================================================
            # MULTICLASS
            # =================================================
            if self.multiclass:
                pred = np.argmax(probs)
                y_probs.append(probs.flatten())
            # =================================================
            # BINARY
            # =================================================
            else:
                pred = 1 if probs[0][0] >= threshold else 0
                y_probs.append(probs[0][0])
            y_preds.append(pred)
        return np.array(y_probs), np.array(y_preds)

    # ========================================================
    # METRICS
    # ========================================================
    def compute_metrics(self, y_true, y_pred):
        if len(y_true.shape) > 1:
            y_true = np.argmax(y_true, axis=1)

        precision = precision_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )

        recall = recall_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )

        f1 = f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0
        )

        acc = accuracy_score(
            y_true,
            y_pred
        )

        return {
            "accuracy": acc,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }

    # ========================================================
    # TEST
    # ========================================================
    def test(self, X_test, y_test, threshold=0.5):
        y_probs, y_preds = self.predict(X_test, threshold)
        metrics = self.compute_metrics(y_test, y_preds)
        return {
            "metrics": metrics,
            "y_pred": y_preds,
            "y_prob": y_probs
        }

    # ========================================================
    # PLOT LOSS
    # ========================================================
    def plot_loss(self):
        plt.figure(figsize=(8,5))
        plt.plot(self.loss_epochs)
        plt.title("Training Loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.grid(True)
        plt.show()

    def plot_train_val_loss(self):
        plt.figure(figsize=(8,5))
        plt.plot(
            self.loss_epochs,
            label="Train Loss",
            linewidth=2
        )
        plt.plot(
            self.val_loss_epochs,
            label="Validation Loss",
            linewidth=2
        )
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.title("Training vs Validation Loss")
        plt.legend()
        plt.grid(True)
        plt.show()

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================
    def confusion_matrix(self, y_true, y_pred):
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        # one-hot -> class index
        if len(y_true.shape) > 1:
            y_true = np.argmax(y_true, axis=1)
        n_classes = len(np.unique(y_true))
        cm = np.zeros((n_classes, n_classes), dtype=int)
        for t, p in zip(y_true, y_pred):
            cm[t, p] += 1
        return cm
    
    # ========================================================
    # PLOT CONFUSION MATRIX
    # ========================================================
    def plot_confusion_matrix(self, y_true, y_pred):
        cm = self.confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(8,6))
        plt.imshow(cm, cmap="Blues")
        plt.title("Confusion Matrix")
        plt.xlabel("Predicted")
        plt.ylabel("True")
        classes = np.arange(cm.shape[0])
        plt.xticks(classes)
        plt.yticks(classes)
        # values inside cells
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(
                    j,
                    i,
                    str(cm[i, j]),
                    ha="center",
                    va="center",
                    color="white" if cm[i, j] > cm.max()/2 else "black"
                )
        plt.colorbar()
        plt.grid(False)
        plt.tight_layout()
        plt.show()
