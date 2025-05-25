# main.py
# 메인 학습 스크립트

import torch
import torch.optim.lr_scheduler as lr_scheduler
import os
from datetime import datetime

# 모듈 import (상대 import 사용)
from .config import CONFIG, seed_everything
from .models import SymmetricResidualCategoryNCF
from .data_utils import load_data, create_dataloaders, load_pretrained_vectors, analyze_data_sparsity
from .evaluation import train_epoch, validate_epoch, evaluate_comprehensive
from .utils import save_checkpoint, visualize_training_extended

def main():
    print("Practical Residual NCF v5 시작")
    
    # 재현성을 위한 시드 고정
    seed_everything(CONFIG['seed'])
    print(f"Device: {CONFIG['device']}")
    
    # 데이터 로딩
    data = load_data()
    
    # 데이터 희소성 분석 (학습 전 수행)
    sparsity_info = analyze_data_sparsity(data['interactions'], data['n_users'], data['n_items'])
    
    data_loaders = create_dataloaders(data, CONFIG)
    
    train_loader = data_loaders['train_loader']
    val_loader = data_loaders['val_loader']
    test_loader = data_loaders['test_loader']
    test_interactions = data_loaders['test_interactions']  # 평가용 테스트 데이터
    
    # 모델 초기화
    device = torch.device(CONFIG['device'])
    model = SymmetricResidualCategoryNCF(
        n_users=data['n_users'],
        n_items=data['n_items'],
        config=CONFIG
    ).to(device)
    
    # 모델 파라미터 수 출력
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"학습 가능한 파라미터: {total_params:,}개")
    
    # 사전학습 벡터 로드
    load_pretrained_vectors(model, data['vectors'])
    
    # 옵티마이저 및 스케줄러 설정 (별도 LR)
    # 아이템 벡터와 나머지 파라미터 분리
    item_params = [model.item_vector_full.weight]
    other_params = [p for p in model.parameters() if p is not model.item_vector_full.weight and p.requires_grad]
    
    optimizer = torch.optim.Adam([
        {'params': other_params, 'lr': CONFIG['learning_rate'], 'weight_decay': CONFIG['weight_decay']},
        {'params': item_params, 'lr': CONFIG['item_lr'], 'weight_decay': 0}  # 아이템 벡터는 weight decay 없음
    ])
    
    scheduler = lr_scheduler.ReduceLROnPlateau(
        optimizer, 
        mode='max',
        factor=0.5, 
        patience=CONFIG['patience'],
        verbose=True
    )
    
    # 학습 루프
    best_hr10 = 0
    print(f"\n학습 시작 (총 {CONFIG['epochs']} 에폭)")
    
    # 학습 이력 추적 (확장 + Validation Loss)
    history = {
        'epochs': [],
        'train_loss': [],
        'val_loss': [],           # Validation Loss 추가
        'eval_epochs': [],
        'HR@5': [], 'HR@10': [], 'HR@20': [],
        'Recall@5': [], 'Recall@10': [], 'Recall@20': [],
        'NDCG@5': [], 'NDCG@10': [], 'NDCG@20': [],
        'MAP@5': [], 'MAP@10': [], 'MAP@20': [],
        'AUC': [],
        'learning_rates': []
    }
    
    for epoch in range(CONFIG['epochs']):
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss = validate_epoch(model, val_loader, device)  # Validation Loss 계산
        
        # 학습 이력 기록 (매 에폭)
        history['epochs'].append(epoch)
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)  # Val Loss 기록
        
        if epoch % CONFIG['eval_every'] == 0:
            # 핵심 수정: 테스트 데이터만으로 평가 수행
            comprehensive_metrics = evaluate_comprehensive(
                model, 
                test_interactions,  # ← 전체 데이터가 아닌 테스트 데이터만 사용!
                data['user_id_to_idx'], 
                data['item_id_to_model_idx'], 
                device, 
                k_list=[5, 10, 20]
            )
            
            print(f"Epoch {epoch:3d}: Train={train_loss:.4f}, Val={val_loss:.4f}")
            print(f"  HR@10={comprehensive_metrics['HR@10']:.4f}, NDCG@10={comprehensive_metrics['NDCG@10']:.4f}, MAP@10={comprehensive_metrics['MAP@10']:.4f}")
            
            # 평가 이력 기록
            history['eval_epochs'].append(epoch)
            history['HR@5'].append(comprehensive_metrics['HR@5'])
            history['HR@10'].append(comprehensive_metrics['HR@10'])
            history['HR@20'].append(comprehensive_metrics['HR@20'])
            history['Recall@5'].append(comprehensive_metrics['Recall@5'])
            history['Recall@10'].append(comprehensive_metrics['Recall@10'])
            history['Recall@20'].append(comprehensive_metrics['Recall@20'])
            history['NDCG@5'].append(comprehensive_metrics['NDCG@5'])
            history['NDCG@10'].append(comprehensive_metrics['NDCG@10'])
            history['NDCG@20'].append(comprehensive_metrics['NDCG@20'])
            history['MAP@5'].append(comprehensive_metrics['MAP@5'])
            history['MAP@10'].append(comprehensive_metrics['MAP@10'])
            history['MAP@20'].append(comprehensive_metrics['MAP@20'])
            history['AUC'].append(comprehensive_metrics['AUC'])
            
            # 현재 LR 출력 (두 그룹)
            current_lrs = [group['lr'] for group in optimizer.param_groups]
            history['learning_rates'].append(current_lrs[0])  # 일반 LR만 기록
            
            # 스케줄러 업데이트 (HR@10 기준)
            scheduler.step(comprehensive_metrics['HR@10'])
            
            # 기존 HR@10 기반 Early Stopping (연속 4번 성능 감소시 조기 종료)
            current_hr10 = comprehensive_metrics['HR@10']
            if len(history['HR@10']) >= CONFIG['patience']:
                recent_hr10 = history['HR@10'][-CONFIG['patience']:]
                if all(recent_hr10[i] >= recent_hr10[i+1] for i in range(len(recent_hr10)-1)):
                    print(f"Early Stopping: 연속 {CONFIG['patience']}회 성능 감소")
                    break
            
            # 최고 성능 모델 저장
            if comprehensive_metrics['HR@10'] > best_hr10:
                best_hr10 = comprehensive_metrics['HR@10']
                save_checkpoint(model, optimizer, epoch, 
                              os.path.join(CONFIG['save_dir'], 'best_model_v5_modular.pth'))
                print(f"새로운 최고 성능! HR@10: {best_hr10:.4f}")
        else:
            print(f"Epoch {epoch:3d}: Train={train_loss:.4f}, Val={val_loss:.4f}")
    
    print(f"\n학습 완료! 최고 HR@10: {best_hr10:.4f}")
    
    # 최종 결과 시각화
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(CONFIG['save_dir'], f'training_results_modular_{timestamp}.png')
    visualize_training_extended(history, save_path) 