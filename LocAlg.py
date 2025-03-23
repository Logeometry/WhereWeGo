import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(n_samples=500,
                           n_features=2,
                           n_classes=3,
                           n_clusters_per_class=1,
                           n_informative=2,
                           n_redundant=0,
                           random_state=40)

plt.scatter(X[:, 0], X[:, 1], marker='o', c=y, s=100, edgecolor="k", linewidth=1)
plt.xlabel("x_1")
plt.ylabel("x_2")
plt.show()

# Training/Testing Dataset 분리 (80:20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1234)

print("Training samples: ", len(X_train))
print("Testing samples: ", len(X_test))

def L2_distance(x1, x2):
  return np.sqrt(np.sum((x1 - x2) ** 2))

class KNN:
  def __init__(self, k=3):
    # initialization
    self.k = k
    self.X_train = None
    self.y_train = None

  def fit(self, X, y):
    # Storage training datas
    self.X_train = X
    self.y_train = y  #저장해야할 정보가 들어가 있음


  def predict(self, X):
    # Prediction
    y_pred = []

    for input in X:
      distance=[]
      for train in self.X_train:
          distance.append( L2_distance(input, train))

      index = np.argsort(distance)[:self.k] #가까운 index를 반환
      label = []


      for i in index:
        label.append(self.y_train[i])

      prediction = max(label , key = label.count)   #개수가 많은걸로 키를 지정해서 뽑겠다
      y_pred.append(prediction)

    return y_pred





    # Dis= []
    # label = []
    # for i in range (X)
    #   for c in range (X_train)
    #     Dis.append(L2_distance(np.sum((X - X_train) ** 2)))   #전체 데이터 셋 X에서 X_train 만큼 각각의 distance를 구한 값을 저장하겠다.

    # Dis = np.argsort(Dis)[:self.k]     #가장 가까운 3개만 가져오겠다
    # label= max(Dis , key = Dis.count)    #가져온 3개중에서 가장 개수가 많은걸로 확률을 구한다



    # for z in range(y)
    #   for v in range(y_train)
    #     label.append(L2_distance((y-y_train) ** 2))



model = KNN()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

accuracy = np.sum(y_pred == y_test) / len(y_test)
print(accuracy)

plt.figure(figsize=(12,4))

plt.subplot(1, 2, 1)
plt.title("label")
plt.scatter(X_test[:, 0], X_test[:, 1], marker='o', c=y_test, s=100, edgecolor="k", linewidth=1)

plt.subplot(1, 2, 2)
plt.title("prediction")
plt.scatter(X_test[:, 0], X_test[:, 1], marker='o', c=y_pred, s=100, edgecolor="k", linewidth=1)
plt.show()

X, y = make_classification(n_samples=500,
                           n_features=2,
                           n_classes=4,
                           n_clusters_per_class=1,
                           n_informative=2,
                           n_redundant=0,
                           random_state=40)

X[:, 0] = X[:, 0] * 0.1 - 100
X[:, 1] = X[:, 1] * 100 + 120

plt.scatter(X[:, 0], X[:, 1], marker='o', c=y, s=100, edgecolor="k", linewidth=1)
plt.xlabel("x_1")
plt.ylabel("x_2")
plt.show()

# Training/Testing Dataset 분리 (80:20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1234)

print("Training samples: ", len(X_train))
print("Testing samples: ", len(X_test))

model = KNN(k=1)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

accuracy = np.sum(y_pred == y_test) / len(y_test)
print(accuracy)
