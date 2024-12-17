from dataset import *
import numpy as np

class LogisticRegression():
    def __init__(self, num_features, num_classes, learning_rate=0.1, epoch=100):
        self.num_features = num_features
        self.num_classes = num_classes
        self.learning_rate = learning_rate
        self.epoch = epoch

        self.weights = np.random.rand(num_classes, num_features)
        self.bias = np.zeros(self.num_classes)

    def softmax(self, z):
        exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)
    
    def train(self, X, y):
        y_onehot = np.eye(np.max(y) + 1)[y]
        for epoch in range(self.epoch):
            scores = np.dot(X, self.weights.T) + self.bias
            probs = self.softmax(scores)
            loss = -np.mean(np.sum(y_onehot * np.log(probs + 1e-9), axis=1))
            
            # gradient
            grad_w = np.dot((probs - y_onehot).T, X) / X.shape[0]
            grad_b = np.sum(probs - y_onehot, axis=0) / X.shape[0]
            
            self.weights -= self.learning_rate * grad_w
            self.bias -= self.learning_rate * grad_b
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {loss:.4f}")

    def predict(self, X):
        scores = np.dot(X, self.weights.T) + self.bias
        probs = self.softmax(scores)
        return np.argmax(probs, axis=1)
    
if __name__ == "__main__":
    voc_vectors = get_voc_vectors()
    voc_labels = get_voc_labels()

    X, y = [], []
    for voc in voc_vectors.keys():
        X.append(voc_vectors[voc])
        y.append(voc_labels[voc])
    X, y = np.array(X), np.array(y)
    N = X.shape[0]

    train_size = 0.8
    X_train, X_test = X[:int(train_size * N)], X[int(train_size * N):]
    y_train, y_test = y[:int(train_size * N)], y[int(train_size * N):]

    model = LogisticRegression(num_features=300, num_classes=5, learning_rate=0.4, epoch=500)
    model.train(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = np.mean(y_pred == y_test)
    print(f"模型準確率: {accuracy:.2f}")