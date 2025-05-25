# evaluation.py
# 평가 함수 모듈

import torch
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm

def validate_epoch(model, dataloader, device):
    """과적합 감지를 위한 검증 손실 계산"""
    model.eval()
    total_loss = 0
    
    with torch.no_grad():
        for users, items, labels in tqdm(dataloader, desc="Validating"):
            users, items, labels = users.to(device), items.to(device), labels.to(device)
            predictions = model(users, items)
            loss = F.binary_cross_entropy_with_logits(predictions, labels)
            total_loss += loss.item()
    
    return total_loss / len(dataloader)

def train_epoch(model, dataloader, optimizer, device):
    """한 에폭 모델 학습"""
    model.train()
    total_loss = 0
    
    for users, items, labels in tqdm(dataloader, desc="Training"):
        users, items, labels = users.to(device), items.to(device), labels.to(device)
        
        optimizer.zero_grad()
        predictions = model(users, items)
        loss = F.binary_cross_entropy_with_logits(predictions, labels)
        
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)

def calculate_ndcg(y_true, y_score, k=10):
    """NDCG@K 메트릭 계산"""
    def dcg_at_k(r, k):
        r = np.asfarray(r)[:k]
        return np.sum(r / np.log2(np.arange(2, r.size + 2)))
    
    indices = np.argsort(y_score)[::-1]
    ranked_true = y_true[indices]
    dcg = dcg_at_k(ranked_true, k)
    idcg = dcg_at_k(sorted(y_true, reverse=True), k)
    
    return dcg / idcg if idcg > 0 else 0

def calculate_map(y_true, y_score, k=10):
    """MAP@K (평균 정밀도) 메트릭 계산"""
    indices = np.argsort(y_score)[::-1][:k]
    ranked_true = y_true[indices]
    
    precisions = []
    num_hits = 0
    
    for i, hit in enumerate(ranked_true):
        if hit:
            num_hits += 1
            precision_at_i = num_hits / (i + 1)
            precisions.append(precision_at_i)
    
    return np.mean(precisions) if precisions else 0.0

def evaluate_comprehensive(model, interactions, user_id_to_idx, item_id_to_model_idx, device, k_list=[5, 10, 20]):
    """
    다중 메트릭을 사용한 종합 평가
    
    주어진 k 값들에 대해 HR, Recall, NDCG, MAP, AUC를 계산합니다.
    
    Args:
        model: 학습된 모델
        interactions: 평가용 사용자-아이템 상호작용
        user_id_to_idx: 사용자 ID에서 인덱스로의 매핑
        item_id_to_model_idx: 아이템 ID에서 모델 인덱스로의 매핑
        device: 연산 장치
        k_list: 평가할 k 값들의 리스트
        
    Returns:
        dict: 계산된 모든 메트릭을 포함하는 딕셔너리
    """
    model.eval()
    
    user_positive_items = {}
    all_item_indices = list(item_id_to_model_idx.values())
    
    # 유저별 positive 아이템 수집
    for user_id, item_list in interactions.items():
        if user_id in user_id_to_idx:
            user_idx = user_id_to_idx[user_id]
            positive_items = []
            for item_id in item_list:
                if item_id in item_id_to_model_idx:
                    positive_items.append(item_id_to_model_idx[item_id])
            if positive_items:
                user_positive_items[user_idx] = set(positive_items)
    
    # 메트릭 초기화
    metrics = {}
    for k in k_list:
        metrics[f'HR@{k}'] = []
        metrics[f'Recall@{k}'] = []
        metrics[f'NDCG@{k}'] = []
        metrics[f'MAP@{k}'] = []
    
    metrics['AUC'] = []
    
    with torch.no_grad():
        for user_idx in tqdm(user_positive_items.keys(), desc="Evaluating"):
            positive_items = user_positive_items[user_idx]
            
            # 해당 유저와 모든 아이템 조합 생성
            user_tensor = torch.tensor([user_idx] * len(all_item_indices), device=device)
            items_tensor = torch.tensor(all_item_indices, device=device)
            
            # 예측 점수 계산
            predictions = torch.sigmoid(model(user_tensor, items_tensor))
            predictions_np = predictions.cpu().numpy()
            
            # Ground truth 배열 생성
            y_true = np.array([1 if item_idx in positive_items else 0 for item_idx in all_item_indices])
            
            # AUC 계산
            try:
                from sklearn.metrics import roc_auc_score
                auc = roc_auc_score(y_true, predictions_np)
                metrics['AUC'].append(auc)
            except:
                pass
            
            # 상위 K개 아이템 인덱스 획득
            top_indices = np.argsort(predictions_np)[::-1]
            
            # 각 K에 대해 메트릭 계산
            for k in k_list:
                top_k_indices = top_indices[:k]
                top_k_items = set([all_item_indices[idx] for idx in top_k_indices])
                
                # HR@K
                hit = 1 if len(top_k_items & positive_items) > 0 else 0
                metrics[f'HR@{k}'].append(hit)
                
                # Recall@K
                recall = len(top_k_items & positive_items) / len(positive_items)
                metrics[f'Recall@{k}'].append(recall)
                
                # NDCG@K
                y_true_k = y_true[top_k_indices]
                y_score_k = predictions_np[top_k_indices]
                ndcg = calculate_ndcg(y_true_k, y_score_k, k)
                metrics[f'NDCG@{k}'].append(ndcg)
                
                # MAP@K
                map_score = calculate_map(y_true_k, y_score_k, k)
                metrics[f'MAP@{k}'].append(map_score)
    
    # 평균 계산
    final_metrics = {}
    for metric_name, values in metrics.items():
        if values:
            avg_value = np.mean(values)
            final_metrics[metric_name] = avg_value
    
    return final_metrics 