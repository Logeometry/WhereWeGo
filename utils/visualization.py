import torch
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
"""
학습된 벡터의 시각화를 위한 파일입니다.
line12: np.load('model_path.npy)이니 model_path.npy만 수정해 진행하십시오
만약 모델이 파이토치 모델이라면 line12를 주석처리하고 line13을 진행하십시오
line13: torch.load('model_path.pt)이니 model_path.pt만 수정해 진행하십시오
"""
# 저장된 데이터 불러오기
item_embeddings = np.load('C:\WhereWeGo\embeddings\item_embeddings_dim256.npy')
#item_embeddings = torch.load('model_path.pt)

# t-SNE 변환
tsne = TSNE(n_components=2, random_state=42)
reduced = tsne.fit_transform(item_embeddings)

# 시각화
plt.figure(figsize=(10, 8))
plt.scatter(reduced[:, 0], reduced[:, 1], alpha=0.6)
plt.title("Item Embedding t-SNE")
plt.xlabel("dim 1")
plt.ylabel("dim 2")
plt.grid(True)
plt.show()
