from collections import Counter

import matplotlib.pyplot as plt
import numpy as np


class Kfold:

    def __init__(self, k=5, shuffle=True, random_state = 42):
        self.k = k
        self.shuffle = shuffle
        self.random_state = random_state

    def shuffle_data(self, X, y):
        indices = np.arange(X.shape[0])
        np.random.seed(self.random_state)
        np.random.shuffle(indices)
        return X[indices], y[indices]

    def get_folds(self, X, y):
        if self.shuffle:
          X, y = self.shuffle_data(X, y)
        fold_size = X.shape[0] // self.k

        folds = {}

        for i in range(self.k):
          start = i * fold_size
          end = start + fold_size

          X_val = X[start:end]
          y_val = y[start:end]

          X_train = np.concatenate([X[:start], X[end:]])
          y_train = np.concatenate([y[:start], y[end:]])

          folds[i] = {
              "X_train": X_train,
              "y_train": y_train,
              "X_val": X_val,
              "y_val": y_val
          }

        return folds

    def get_stratified_folds(self, X, y):
        if self.shuffle:
            X, y = self.shuffle_data(X, y)

        folds = {i: {"X_train": [], "y_train": [], "X_val": [], "y_val": []} for i in range(self.k)}

        for class_ in np.unique(y):
            class_idx = np.where(y == class_)[0]
            X_class = X[class_idx]
            y_class = y[class_idx]
            fold_size = X_class.shape[0] // self.k

            for i in range(self.k):
                start = i * fold_size
                end = start + fold_size

                X_val = X_class[start:end]
                y_val = y_class[start:end]

                X_train = np.concatenate([X_class[:start], X_class[end:]])
                y_train = np.concatenate([y_class[:start], y_class[end:]])

                folds[i]["X_train"].append(X_train)
                folds[i]["y_train"].append(y_train)
                folds[i]["X_val"].append(X_val)
                folds[i]["y_val"].append(y_val)

        # juntar todas as classes em cada fold
        for i in range(self.k):
            folds[i]["X_train"] = np.concatenate(folds[i]["X_train"])
            folds[i]["y_train"] = np.concatenate(folds[i]["y_train"])
            folds[i]["X_val"] = np.concatenate(folds[i]["X_val"])
            folds[i]["y_val"] = np.concatenate(folds[i]["y_val"])

        return folds

    def plot_folds_distribution(self, folds, type_="", colors=None):
        if colors is None:
            colors = {0: "green", 1: "red"}  # default

        k = len(folds)

        train_class0 = []
        train_class1 = []
        val_class0 = []
        val_class1 = []

        for i in range(k):
            y_train = folds[i]["y_train"]
            y_val = folds[i]["y_val"]

            train_counts = Counter(y_train)
            val_counts = Counter(y_val)

            total_train = len(y_train)
            total_val = len(y_val)

            train_class0.append(train_counts.get(0, 0) / total_train)
            train_class1.append(train_counts.get(1, 0) / total_train)

            val_class0.append(val_counts.get(0, 0) / total_val)
            val_class1.append(val_counts.get(1, 0) / total_val)

        x = np.arange(k)

        # ---- TRAIN ----
        plt.figure()
        bars_c0 = plt.bar(x, train_class0, label='Class 0', color=colors.get(0, "gray"))
        bars_c1 = plt.bar(
            x,
            train_class1,
            bottom=train_class0,
            label='Class 1',
            color=colors.get(1, "gray")
        )

        for i in range(k):
            if train_class0[i] > 0:
                plt.text(x[i], train_class0[i] / 2,
                        f"{train_class0[i]*100:.0f}%",
                        ha='center', va='center')

            if train_class1[i] > 0:
                plt.text(x[i],
                        train_class0[i] + train_class1[i] / 2,
                        f"{train_class1[i]*100:.0f}%",
                        ha='center', va='center')

        plt.ylim(0, 1)
        plt.xticks(x, [f"Fold {i}" for i in range(k)])
        plt.title(f"TRAIN - proporção por classe {type_}")
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.show()

        # ---- VALIDATION ----
        plt.figure()
        bars_c0 = plt.bar(x, val_class0, label='Class 0', color=colors.get(0, "gray"))
        bars_c1 = plt.bar(
            x,
            val_class1,
            bottom=val_class0,
            label='Class 1',
            color=colors.get(1, "gray")
        )

        for i in range(k):
            if val_class0[i] > 0:
                plt.text(x[i], val_class0[i] / 2,
                        f"{val_class0[i]*100:.0f}%",
                        ha='center', va='center')

            if val_class1[i] > 0:
                plt.text(x[i],
                        val_class0[i] + val_class1[i] / 2,
                        f"{val_class1[i]*100:.0f}%",
                        ha='center', va='center')

        plt.ylim(0, 1)
        plt.xticks(x, [f"Fold {i}" for i in range(k)])
        plt.title(f"VALIDATION - proporção por classe {type_}")
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.show()
        