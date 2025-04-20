import numpy as np
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import os
import time
import copy
import random
from tqdm import tqdm
from datetime import datetime
import matplotlib.pyplot as plt
"""
이 버전은 논문과 더 유사한 설정을 따르는 BPR 구현임.

변경 사항:
- 최적화 함수: Adam → S.G.D
- 학습률: 0.01 → 0.05
- 임베딩 초기화: 0.001 → 0.1
- 학습률 감소 스케줄러 → L2 정규화 도입
    user_reg: 0.0025
    item_reg: 0.00025

정규화 계수는 사용자 임베딩에 더 크게 적용되었음
이는 개인화 추천에서 유저 벡터가 각기 다른 사용자 특성을 학습하기 때문
과적합을 방지하기 위한 조치로 사용
반면, 아이템 벡터는 여러 사용자가 공유하는 정보임
상대적으로 일반화가 쉬워 더 약한 정규화를 적용함.
"""
class BPRDataset(Dataset):
    def __init__(self, triplet_file):
        """
        트리플렛 파일로부터 BPR 데이터셋 생성
        
        Args:
            triplet_file: 트리플렛 JSON 파일 경로
        """
        start_time = time.time()
        
        print(f"데이터셋 로드 중: {triplet_file}")
        with open(triplet_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.triplets = data['triplets']
        self.metadata = data['metadata']
        self.user_id_map = data.get('user_id_map', {})
        self.business_id_map = data.get('business_id_map', {})
        
        # 데이터셋 정보 출력
        print(f"데이터셋 로드 완료:")
        print(f"- 총 트리플렛 수: {len(self.triplets)}")
        print(f"- 사용자 수: {self.metadata.get('num_users', 0)}")
        print(f"- 비즈니스 수: {self.metadata.get('num_businesses', 0)}")
        
        # NumPy 배열로 변환
        if isinstance(self.triplets[0], list):
            self.data = np.array(self.triplets, dtype=np.int64)
        else:
            # triplets가 딕셔너리 형태인 경우
            self.data = np.array([[t.get('user', 0), t.get('item', 0), t.get('rating', 0)] 
                               for t in self.triplets], dtype=np.int64)
        
        # Positive와 Negative 샘플 분리
        self.pos_samples = self.data[self.data[:, 2] == 1]
        self.neg_samples = self.data[self.data[:, 2] == 0]
        
        # 추가: 사용자별 상호작용 정보 구성 (LearnBPR 알고리즘 위함)
        self.user_pos_items = {}
        self.user_neg_items = {}
        
        # 사용자별 긍정/부정 상호작용 항목 정리
        for user_id in np.unique(self.pos_samples[:, 0]):
            user_id = int(user_id)
            # 현재 사용자의 모든 positive 상호작용
            pos_items = self.pos_samples[self.pos_samples[:, 0] == user_id][:, 1]
            self.user_pos_items[user_id] = pos_items
            
            # 현재 사용자의 모든 negative 상호작용
            neg_items = self.neg_samples[self.neg_samples[:, 0] == user_id][:, 1]
            if len(neg_items) > 0:
                self.user_neg_items[user_id] = neg_items
            else:
                # 명시적인 negative 상호작용이 없는 경우 모든 non-positive 항목을 negative로 간주
                num_items = self.metadata.get('num_businesses', 0)
                self.user_neg_items[user_id] = np.setdiff1d(np.arange(num_items), pos_items)
        
        print(f"- Positive 샘플: {len(self.pos_samples)}")
        print(f"- Negative 샘플: {len(self.neg_samples)}")
        print(f"- 사용자 수: {len(self.user_pos_items)}")
        print(f"- 데이터 로딩 시간: {time.time() - start_time:.2f}초")
    
    def get_user_data(self):
        """
        LearnBPR 알고리즘을 위한 사용자 데이터 반환
        """
        return {
            'users': list(self.user_pos_items.keys()),
            'user_pos_items': self.user_pos_items,
            'user_neg_items': self.user_neg_items
        }
    
    def __len__(self):
        return len(self.pos_samples)
    
    def __getitem__(self, idx):
        # Positive 샘플 가져오기
        user_id, pos_item, _ = self.pos_samples[idx]
        user_id = int(user_id)
        
        # Negative 샘플 선택
        if user_id in self.user_neg_items and len(self.user_neg_items[user_id]) > 0:
            neg_items = self.user_neg_items[user_id]
            neg_item = np.random.choice(neg_items)
        else:
            # 극단적인 경우: 모든 아이템이 positive인 경우
            num_items = self.metadata.get('num_businesses', 10000)
            neg_item = np.random.randint(0, num_items)
        
        return {
            'user': torch.tensor([user_id], dtype=torch.long),
            'pos_item': torch.tensor([pos_item], dtype=torch.long),
            'neg_item': torch.tensor([neg_item], dtype=torch.long)
        }


# 2. BPR 모델 정의
class BPRModel(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=128):
        """
        Bayesian Personalized Ranking 모델
        
        Args:
            num_users: 사용자 수
            num_items: 아이템(비즈니스) 수
            embedding_dim: 임베딩 차원
        """
        super(BPRModel, self).__init__()
        
        self.embedding_dim = embedding_dim
        print(f"BPRModel 초기화: 임베딩 차원 = {embedding_dim}")
        
        # 사용자 임베딩
        self.user_embeddings = nn.Embedding(num_users, embedding_dim)
        # 아이템 임베딩
        self.item_embeddings = nn.Embedding(num_items, embedding_dim)
        
        # 임베딩 초기화 (논문의 평균 0, 표준편차 0.1 설정)
        nn.init.normal_(self.user_embeddings.weight, std=0.1)
        nn.init.normal_(self.item_embeddings.weight, std=0.1)
        
        # 차원 저장
        self.num_users = num_users
        self.num_items = num_items
    
    def forward(self, user, pos_item, neg_item):
        """
        BPR 모델 포워드 패스
        
        Args:
            user: 사용자 인덱스
            pos_item: 긍정적 아이템 인덱스
            neg_item: 부정적 아이템 인덱스
            
        Returns:
            x_uij: 긍정적 아이템과 부정적 아이템 간의 점수 차이
            user_embedding: 사용자 임베딩
            pos_item_embedding: 긍정적 아이템 임베딩
            neg_item_embedding: 부정적 아이템 임베딩
        """
        # 임베딩 검색
        user_embedding = self.user_embeddings(user)
        pos_item_embedding = self.item_embeddings(pos_item)
        neg_item_embedding = self.item_embeddings(neg_item)
        
        # 점수 계산
        pos_scores = torch.sum(user_embedding * pos_item_embedding, dim=-1)
        neg_scores = torch.sum(user_embedding * neg_item_embedding, dim=-1)
        
        # 논문에서의 x_uij 명시적 계산
        x_uij = pos_scores - neg_scores
        
        return x_uij, user_embedding, pos_item_embedding, neg_item_embedding
    
    def predict(self, user_indices, item_indices=None):
        """
        사용자-아이템 점수 예측
        """
        device = self.user_embeddings.weight.device
        
        # 단일 사용자, 모든 아이템 점수 계산
        if item_indices is None:
            users = torch.tensor([user_indices], dtype=torch.long, device=device)
            user_embedding = self.user_embeddings(users)
            all_item_embeddings = self.item_embeddings.weight
            
            scores = torch.matmul(user_embedding, all_item_embeddings.t())
            return scores.squeeze()
        
        # 지정된 사용자-아이템 페어 점수 계산
        users = torch.tensor(user_indices, dtype=torch.long, device=device)
        items = torch.tensor(item_indices, dtype=torch.long, device=device)
        
        user_embedding = self.user_embeddings(users)
        item_embedding = self.item_embeddings(items)
        
        return torch.sum(user_embedding * item_embedding, dim=-1)


# 3. BPR 손실 함수 (논문에 충실한 버전)
class BPRLoss(nn.Module):
    def __init__(self):
        super(BPRLoss, self).__init__()
    
    def forward(self, x_uij, user_emb=None, pos_item_emb=None, neg_item_emb=None, lambda_u=0.0025, lambda_i=0.00025):
        """
        BPR 손실 계산: -ln(sigmoid(x_uij)) + λ_u * ||u||² + λ_i * (||i||² + ||j||²)
        
        Args:
            x_uij: 사용자 u가 아이템 i를 아이템 j보다 선호하는 정도
            user_emb: 사용자 임베딩
            pos_item_emb: 긍정적 아이템 임베딩
            neg_item_emb: 부정적 아이템 임베딩
            lambda_u: 사용자 임베딩에 대한 정규화 계수
            lambda_i: 아이템 임베딩에 대한 정규화 계수
            
        Returns:
            손실값
        """
        # 수치 안정성을 위한 epsilon
        epsilon = 1e-8
        
        # 논문에서 제시한 손실 함수 (식 8)
        bpr_loss = -torch.log(torch.sigmoid(x_uij) + epsilon)
        
        # 분리된 정규화 적용 (식 9~11)
        if user_emb is not None and pos_item_emb is not None and neg_item_emb is not None:
            user_reg = lambda_u * torch.norm(user_emb, p=2, dim=1)
            pos_item_reg = lambda_i * torch.norm(pos_item_emb, p=2, dim=1)
            neg_item_reg = lambda_i * torch.norm(neg_item_emb, p=2, dim=1)
            
            # 총 손실 = BPR 손실 + 사용자 정규화 + 아이템 정규화
            total_loss = bpr_loss + user_reg + pos_item_reg + neg_item_reg
            return total_loss.mean()
        
        return bpr_loss.mean()


# 5. 평가 함수
def evaluate_model(model, dataset, top_k=10, num_users=100, device="cuda" if torch.cuda.is_available() else "cpu", verbose=True):
    """
    모델 성능 평가
    
    Args:
        model: 평가할 BPR 모델
        dataset: 데이터셋
        top_k: 추천 아이템 수
        num_users: 평가할 사용자 수
        device: 계산 장치
        verbose: 상세 출력 여부
    
    Returns:
        평가 지표 딕셔너리
    """
    model.eval()
    model = model.to(device)
    
    # 평가할 사용자 선택
    user_data = dataset.get_user_data()
    users = user_data['users']
    user_pos_items = user_data['user_pos_items']
    
    if num_users is not None and num_users < len(users):
        eval_users = np.random.choice(users, num_users, replace=False)
    else:
        eval_users = users
    
    # 평가 지표
    metrics = {
        f'MAP@{top_k}': [],
        f'Recall@{top_k}': [],
        f'NDCG@{top_k}': []
    }
    
    if verbose:
        print(f"\n평가 중 ({len(eval_users)} 사용자)...")
        progress_bar = tqdm(eval_users)
    else:
        progress_bar = eval_users
    
    with torch.no_grad():
        for u in progress_bar:
            # 학습 아이템 (마스킹용)
            train_items = user_pos_items[u]
            
            # 테스트 세트 생성 (학습 아이템의 20%를 테스트용으로 분리)
            np.random.shuffle(train_items)
            split_idx = int(len(train_items) * 0.8)
            test_items = train_items[split_idx:]
            actual_train_items = train_items[:split_idx]
            
            if len(test_items) == 0:
                continue
                
            # 사용자의 모든 아이템 점수 예측
            scores = model.predict(u)
            scores = scores.cpu().numpy()
            
            # 학습 아이템 마스킹
            scores[actual_train_items] = -np.inf
            
            # Top-K 추천 아이템
            recommended_items = np.argsort(-scores)[:top_k]
            
            # 평가 지표 계산
            # MAP@K
            precision = len(set(recommended_items) & set(test_items)) / top_k
            metrics[f'MAP@{top_k}'].append(precision)
            
            # Recall@K
            recall = len(set(recommended_items) & set(test_items)) / len(test_items)
            metrics[f'Recall@{top_k}'].append(recall)
            
            # NDCG@K 계산
            dcg = 0
            for i, item in enumerate(recommended_items):
                if item in test_items:
                    dcg += 1 / np.log2(i + 2)
            
            idcg = 0
            for i in range(min(len(test_items), top_k)):
                idcg += 1 / np.log2(i + 2)
            
            ndcg = dcg / idcg if idcg > 0 else 0
            metrics[f'NDCG@{top_k}'].append(ndcg)
    
    # 평균 지표 계산
    avg_metrics = {}
    for metric, values in metrics.items():
        if values:
            avg_metrics[metric] = np.mean(values)
        else:
            avg_metrics[metric] = 0.0
    
    # 결과 출력
    if verbose:
        print("\n평가 결과:")
        for metric, value in avg_metrics.items():
            print(f"- {metric}: {value:.4f}")
    
    return avg_metrics


# 성능 지표 시각화 함수 추가
def plot_metrics(epochs, metrics_history, save_path="./bpr_model/performance_metrics.png"):
    """
    학습 과정의 성능 지표를 시각화
    
    Args:
        epochs: 에포크 리스트
        metrics_history: 에포크별 성능 지표 기록
        save_path: 그래프 저장 경로
    """
    plt.figure(figsize=(15, 6))
    
    # 지표별 색상 정의
    colors = {
        'MAP': 'blue',
        'Recall': 'red',
        'NDCG': 'green'
    }
    
    # 각 지표별 그래프 그리기
    for metric_name in ['MAP', 'Recall', 'NDCG']:
        metric_values = [metrics[f"{metric_name}@10"] for metrics in metrics_history]
        plt.plot(epochs, metric_values, f"-o", color=colors[metric_name], label=f"{metric_name}@10")
    
    plt.xlabel('Epoch')
    plt.ylabel('Metric Value')
    plt.title('BPR Model Performance Metrics')
    plt.legend()
    plt.grid(True)
    
    # 저장 디렉토리 확인
    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # 그래프 저장
    plt.savefig(save_path)
    print(f"성능 지표 그래프 저장 완료: {save_path}")
    
    return plt


# 4. LearnBPR 알고리즘 구현 (논문에 충실한 방식)
def learn_bpr_algorithm(
    dataset, 
    model,
    num_epochs=50,
    learning_rate=0.05,
    lambda_user=0.0025,
    lambda_item=0.00025,
    num_samples_per_epoch=50000,
    patience=5,
    device="cuda" if torch.cuda.is_available() else "cpu",
    save_path="./bpr_model/original_bpr_model.pt",
    eval_interval=5,  
    eval_users=100    
):
    """
    BPR 논문의 LearnBPR 알고리즘 구현 (Algorithm 1)
    
    Args:
        dataset: BPR 데이터셋
        model: BPR 모델
        num_epochs: 학습 에포크 수
        learning_rate: 학습률
        lambda_user: 사용자 임베딩에 대한 정규화 계수
        lambda_item: 아이템 임베딩에 대한 정규화 계수
        num_samples_per_epoch: 각 에포크당 샘플링할 트리플렛 수
        patience: 검증 손실 향상 없을 때 조기 종료 에포크 수
        device: 학습 장치
        save_path: 모델 저장 경로
        eval_interval: 평가 간격 (에포크)
        eval_users: 평가할 사용자 수
    
    Returns:
        학습된 모델, 손실 리스트, 성능 지표 기록
    """
    print(f"\nLearnBPR 알고리즘으로 학습 시작 (논문 원본 구현)")
    print(f"- 학습률: {learning_rate}")
    print(f"- 사용자 정규화(λ_u): {lambda_user}")
    print(f"- 아이템 정규화(λ_i): {lambda_item}")
    print(f"- 에포크당 샘플 수: {num_samples_per_epoch}")
    print(f"- 평가 간격: {eval_interval} 에포크")
    
    model = model.to(device)
    model.train()
    
    # 손실 함수
    bpr_loss_fn = BPRLoss()
    
    # 데이터 준비
    user_data = dataset.get_user_data()
    users = user_data['users']
    user_pos_items = user_data['user_pos_items']
    user_neg_items = user_data['user_neg_items']
    
    # 학습 통계
    losses = []
    eval_epochs = []
    metrics_history = []
    best_loss = float('inf')
    wait = 0
    best_model = None
    
    # 학습 루프
    for epoch in range(num_epochs):
        start_time = time.time()
        epoch_loss = 0.0
        
        # 각 에포크마다 지정된 수의 (u,i,j) 트리플렛 샘플링
        with tqdm(total=num_samples_per_epoch, desc=f"Epoch {epoch+1}/{num_epochs}") as pbar:
            for sample_idx in range(num_samples_per_epoch):
                # 1. 무작위로 사용자 선택
                u = random.choice(users)
                
                # 사용자가 긍정적/부정적 상호작용이 모두 있는지 확인
                if len(user_pos_items[u]) == 0 or len(user_neg_items[u]) == 0:
                    continue
                
                # 2. 선택한 사용자의 긍정적 아이템 무작위 선택
                i = np.random.choice(user_pos_items[u])
                
                # 3. 선택한 사용자의 부정적 아이템 무작위 선택
                j = np.random.choice(user_neg_items[u])
                
                # 텐서로 변환 및 장치 이동
                u_tensor = torch.tensor([u], dtype=torch.long, device=device)
                i_tensor = torch.tensor([i], dtype=torch.long, device=device)
                j_tensor = torch.tensor([j], dtype=torch.long, device=device)
                
                # 4. 모델 포워드 패스로 x_uij 계산
                x_uij, user_emb, pos_item_emb, neg_item_emb = model(u_tensor, i_tensor, j_tensor)
                
                # 5. BPR 손실 계산 (분리된 정규화 적용)
                loss = bpr_loss_fn(
                    x_uij,
                    user_emb=user_emb,
                    pos_item_emb=pos_item_emb,
                    neg_item_emb=neg_item_emb,
                    lambda_u=lambda_user,
                    lambda_i=lambda_item
                )
                
                # 6. 그래디언트 계산
                # 여기서는 직접 그래디언트를 계산하는 방식 대신 PyTorch의 자동 미분 사용
                
                # 7-9. 매개변수 업데이트 (SGD 방식)
                # 사용자 임베딩 업데이트
                u_grad = torch.autograd.grad(
                    loss, user_emb, retain_graph=True
                )[0]
                model.user_embeddings.weight.data[u] -= learning_rate * u_grad.squeeze()
                
                # 긍정적 아이템 임베딩 업데이트
                i_grad = torch.autograd.grad(
                    loss, pos_item_emb, retain_graph=True
                )[0]
                model.item_embeddings.weight.data[i] -= learning_rate * i_grad.squeeze()
                
                # 부정적 아이템 임베딩 업데이트
                j_grad = torch.autograd.grad(
                    loss, neg_item_emb
                )[0]
                model.item_embeddings.weight.data[j] -= learning_rate * j_grad.squeeze()
                
                epoch_loss += loss.item()
                pbar.update(1)
                
                # 진행 상황 업데이트
                if sample_idx % 1000 == 0:
                    pbar.set_postfix({'loss': epoch_loss / (sample_idx + 1)})
        
        # 에포크 평균 손실
        avg_epoch_loss = epoch_loss / num_samples_per_epoch
        losses.append(avg_epoch_loss)
        
        epoch_time = time.time() - start_time
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {avg_epoch_loss:.6f} - Time: {epoch_time:.2f}s")
        
        # 주기적으로 성능 평가
        if (epoch + 1) % eval_interval == 0 or epoch == num_epochs - 1:
            print(f"\n에포크 {epoch+1} 성능 평가:")
            eval_metrics = evaluate_model(
                model=model,
                dataset=dataset,
                top_k=10,
                num_users=eval_users,
                device=device,
                verbose=True
            )
            
            # 성능 지표 기록
            eval_epochs.append(epoch + 1)
            metrics_history.append(eval_metrics)
        
        # 최고 모델 저장 및 조기 종료 확인
        if avg_epoch_loss < best_loss:
            best_loss = avg_epoch_loss
            best_model = copy.deepcopy(model.state_dict())
            wait = 0
            print(f"  👍 New best model (Loss: {best_loss:.6f})")
        else:
            wait += 1
            if wait >= patience:
                print(f"Early stopping after {epoch+1} epochs (no improvement for {patience} epochs)")
                break
    
    # 최고 모델 복원
    if best_model is not None:
        model.load_state_dict(best_model)
    
    # 손실 그래프 그리기
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, len(losses)+1), losses)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('LearnBPR Training Loss')
    plt.grid(True)
    
    # 저장 디렉토리 확인
    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # 그래프 저장
    plt.savefig(os.path.join(save_dir, 'learnbpr_loss.png'))
    
    # 성능 지표 그래프 그리기
    if metrics_history:
        metrics_plot = plot_metrics(
            eval_epochs, 
            metrics_history, 
            save_path=os.path.join(save_dir, 'learnbpr_metrics.png')
        )
    
    # 모델 저장
    torch.save({
        'model_state': model.state_dict(),
        'losses': losses,
        'metrics_history': metrics_history,
        'eval_epochs': eval_epochs,
        'best_epoch': len(losses) - wait,
        'params': {
            'learning_rate': learning_rate,
            'lambda_user': lambda_user,
            'lambda_item': lambda_item,
            'num_samples_per_epoch': num_samples_per_epoch,
            'final_loss': losses[-1]
        }
    }, save_path)
    
    print(f"모델 저장 완료: {save_path}")
    
    return model, losses, metrics_history


# 6. 메인 실행 함수
def main(
    triplet_file="philly_bpr_triplets.json",
    embedding_dim=128,
    learning_rate=0.05,  # 논문에서는 0.05를 권장
    lambda_user=0.0025,  # 사용자 임베딩 정규화 계수
    lambda_item=0.00025, # 아이템 임베딩 정규화 계수 (사용자보다 작게 설정)
    num_epochs=50,
    num_samples_per_epoch=50000,
    top_k=10,
    eval_users=100,
    eval_interval=5     # 평가 간격 (에포크)
):
    # 데이터셋 로드
    dataset = BPRDataset(triplet_file)
    
    # 모델 초기화
    num_users = dataset.metadata.get('num_users', 0)
    num_items = dataset.metadata.get('num_businesses', 0)
    model = BPRModel(num_users, num_items, embedding_dim)
    
    # 디바이스 설정
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"사용 장치: {device}")
    
    # LearnBPR 알고리즘으로 학습
    model, losses, metrics_history = learn_bpr_algorithm(
        dataset=dataset,
        model=model,
        num_epochs=num_epochs,
        learning_rate=learning_rate,
        lambda_user=lambda_user,
        lambda_item=lambda_item,
        num_samples_per_epoch=num_samples_per_epoch,
        device=device,
        save_path=f"./bpr_model/original_bpr_e{embedding_dim}_lr{learning_rate}_lu{lambda_user}_li{lambda_item}.pt",
        eval_interval=eval_interval,
        eval_users=eval_users
    )
    
    # 모델 평가
    metrics = evaluate_model(
        model=model,
        dataset=dataset,
        top_k=top_k,
        num_users=eval_users,
        device=device
    )
    
    return model, metrics, metrics_history


if __name__ == "__main__":
    print("BPR 논문에 충실한 구현 - LearnBPR 알고리즘 테스트")
    
    # 하이퍼파라미터 설정
    params = {
        'triplet_file': "philly_bpr_triplets.json",
        'embedding_dim': 128,
        'learning_rate': 0.05,
        'lambda_user': 0.0025,
        'lambda_item': 0.00025,
        'num_epochs': 50,
        'num_samples_per_epoch': 50000,
        'top_k': 10,
        'eval_users': 100,
        'eval_interval': 5
    }
    
    # 실행
    model, metrics, metrics_history = main(**params)
    
    # 메트릭 키 미리 생성
    map_key = f"MAP@{params['top_k']}"
    recall_key = f"Recall@{params['top_k']}"
    ndcg_key = f"NDCG@{params['top_k']}"
    
    print("\n학습 및 평가 완료")
    print(f"최종 MAP@{params['top_k']}: {metrics[map_key]:.4f}")
    print(f"최종 Recall@{params['top_k']}: {metrics[recall_key]:.4f}")
    print(f"최종 NDCG@{params['top_k']}: {metrics[ndcg_key]:.4f}") 