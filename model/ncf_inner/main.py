# main.py
# 메인 학습 스크립트 - 계절별 필터링 지원

import torch
import torch.optim.lr_scheduler as lr_scheduler
import os
from datetime import datetime

# 모듈 import (상대 import 사용)
from .config import CONFIG, seed_everything
from .models import SymmetricResidualCategoryNCF
from .data_utils import load_data, create_dataloaders, analyze_data_sparsity
from .evaluation import train_epoch, validate_epoch, evaluate_comprehensive
from .utils import save_checkpoint, visualize_training_extended


def main():
    print("Practical Residual NCF v8 - 계절별 필터링 지원 버전 시작")

    # 재현성을 위한 시드 고정
    seed_everything(CONFIG['seed'])
    print(f"Device: {CONFIG['device']}")

    # 데이터 로딩
    data = load_data()

    # 데이터 희소성 분석 (학습 전 수행)
    sparsity_info = analyze_data_sparsity(data['triplets'], data['n_users'], data['n_items'])

    data_loaders = create_dataloaders(data, CONFIG)

    train_loader = data_loaders['train_loader']
    val_loader = data_loaders['val_loader']
    test_loader = data_loaders['test_loader']
    test_triplets = data_loaders['test_triplets']  # 평가용 테스트 데이터

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

    # 옵티마이저 및 스케줄러 설정 (별도 LR)
    # 아이템 임베딩과 나머지 파라미터 분리
    item_param_names = {
        'item_embedding_gmf.weight',
        'item_embedding_mlp.weight',
        'item_category.weight'
    }

    item_params = []
    other_params = []

    for name, param in model.named_parameters():
        if param.requires_grad:
            if any(item_name in name for item_name in item_param_names):
                item_params.append(param)
            else:
                other_params.append(param)

    optimizer = torch.optim.Adam([
        {'params': other_params, 'lr': CONFIG['learning_rate'], 'weight_decay': CONFIG['weight_decay']},
        {'params': item_params, 'lr': CONFIG['item_lr'], 'weight_decay': 0}  # 아이템 임베딩은 weight decay 없음
    ])

    scheduler = lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='max',
        factor=0.5,
        patience=CONFIG['patience']
    )

    # 학습 루프
    print(f"\n학습 시작 (총 {CONFIG['epochs']} 에폭)")

    # 학습 이력 추적 (확장 + Validation Loss)
    history = {
        'epochs': [],
        'train_loss': [],
        'val_loss': [],  # Validation Loss 추가
        'eval_epochs': [],
        'HR@5': [], 'HR@10': [], 'HR@20': [],
        'Precision@5': [], 'Precision@10': [], 'Precision@20': [],
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

        # 5번째 에폭에 모델 저장
        if epoch == 9:  # 0-based indexing이므로 4가 5번째 에폭
            save_path = os.path.join(CONFIG['save_dir'], f'model_epoch_5.pth')
            save_checkpoint(model, optimizer, epoch, save_path)
            print(f"Epoch 5 모델 저장 완료: {save_path}")

        if epoch % CONFIG['eval_every'] == 0:
            # 핵심 수정: 테스트 데이터만으로 평가 수행
            comprehensive_metrics = evaluate_comprehensive(
                model,
                test_triplets,  # ← triplet 데이터 사용!
                data['user_id_to_idx'],
                data['item_id_to_model_idx'],
                device,
                k_list=[5, 10, 20]
            )

            print(f"Epoch {epoch:3d}: Train={train_loss:.4f}, Val={val_loss:.4f}")

            # 안전한 메트릭 출력
            hr10 = comprehensive_metrics.get('HR@10', 0.0)
            precision10 = comprehensive_metrics.get('Precision@10', 0.0)
            ndcg10 = comprehensive_metrics.get('NDCG@10', 0.0)
            map10 = comprehensive_metrics.get('MAP@10', 0.0)
            print(f"  HR@10={hr10:.4f}, Precision@10={precision10:.4f}, NDCG@10={ndcg10:.4f}, MAP@10={map10:.4f}")

            # 평가 이력 기록 (안전한 방식)
            history['eval_epochs'].append(epoch)
            history['HR@5'].append(comprehensive_metrics.get('HR@5', 0.0))
            history['HR@10'].append(hr10)
            history['HR@20'].append(comprehensive_metrics.get('HR@20', 0.0))
            history['Precision@5'].append(comprehensive_metrics.get('Precision@5', 0.0))
            history['Precision@10'].append(precision10)
            history['Precision@20'].append(comprehensive_metrics.get('Precision@20', 0.0))
            history['Recall@5'].append(comprehensive_metrics.get('Recall@5', 0.0))
            history['Recall@10'].append(comprehensive_metrics.get('Recall@10', 0.0))
            history['Recall@20'].append(comprehensive_metrics.get('Recall@20', 0.0))
            history['NDCG@5'].append(comprehensive_metrics.get('NDCG@5', 0.0))
            history['NDCG@10'].append(ndcg10)
            history['NDCG@20'].append(comprehensive_metrics.get('NDCG@20', 0.0))
            history['MAP@5'].append(comprehensive_metrics.get('MAP@5', 0.0))
            history['MAP@10'].append(map10)
            history['MAP@20'].append(comprehensive_metrics.get('MAP@20', 0.0))
            history['AUC'].append(comprehensive_metrics.get('AUC', 0.0))

            # 현재 LR 출력 (두 그룹)
            current_lrs = [group['lr'] for group in optimizer.param_groups]
            history['learning_rates'].append(current_lrs[0])  # 일반 LR만 기록

            # 스케줄러 업데이트 (Precision@10 기준)
            scheduler.step(precision10)

            # Precision@10 기반 Early Stopping (연속 5번 성능 감소시 조기 종료)
            current_precision10 = precision10
            if len(history['Precision@10']) >= CONFIG['patience']:
                recent_precision10 = history['Precision@10'][-CONFIG['patience']:]
                if all(recent_precision10[i] >= recent_precision10[i + 1] for i in range(len(recent_precision10) - 1)):
                    print(f"Early Stopping: Precision@10 기준으로 연속 {CONFIG['patience']}회 성능 감소")
                    break

        else:
            print(f"Epoch {epoch:3d}: Train={train_loss:.4f}, Val={val_loss:.4f}")

    print(f"\n학습 완료!")

    # 최종 결과 시각화
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(CONFIG['save_dir'], f'training_results_season_{timestamp}.png')
    visualize_training_extended(history, save_path)
