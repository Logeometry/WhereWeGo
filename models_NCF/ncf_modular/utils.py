# utils.py
# 유틸리티 함수 모듈

import torch
import matplotlib.pyplot as plt
import numpy as np
import os


def save_checkpoint(model, optimizer, epoch, path):
    """모델 체크포인트 저장"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)
    print(f"체크포인트 저장 완료: {path}")


def visualize_training_extended(history, save_path):
    """확장된 학습 시각화 - 계절별 필터링 지원"""
    plt.style.use('default')
    fig = plt.figure(figsize=(20, 15))
    fig.suptitle('NCF Training Results - Season-based Filtering Support', fontsize=16, fontweight='bold')

    # 1. Loss Curves
    ax1 = plt.subplot(3, 4, 1)
    if history['train_loss']:
        plt.plot(history['epochs'], history['train_loss'], 'b-', label='Train Loss', linewidth=2)
    if history['val_loss']:
        plt.plot(history['epochs'], history['val_loss'], 'r-', label='Val Loss', linewidth=2)
    plt.title('Training & Validation Loss', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 2. Hit Rate @K
    ax2 = plt.subplot(3, 4, 2)
    for k in [5, 10, 20]:
        if f'HR@{k}' in history and history[f'HR@{k}']:
            plt.plot(history['eval_epochs'], history[f'HR@{k}'],
                     marker='o', linewidth=2, label=f'HR@{k}', markersize=4)
    plt.title('Hit Rate @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Hit Rate')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 3. Precision @K
    ax3 = plt.subplot(3, 4, 3)
    for k in [5, 10, 20]:
        if f'Precision@{k}' in history and history[f'Precision@{k}']:
            plt.plot(history['eval_epochs'], history[f'Precision@{k}'],
                     marker='s', linewidth=2, label=f'Precision@{k}', markersize=4)
    plt.title('Precision @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Precision')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 4. Recall @K
    ax4 = plt.subplot(3, 4, 4)
    for k in [5, 10, 20]:
        if f'Recall@{k}' in history and history[f'Recall@{k}']:
            plt.plot(history['eval_epochs'], history[f'Recall@{k}'],
                     marker='^', linewidth=2, label=f'Recall@{k}', markersize=4)
    plt.title('Recall @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Recall')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 5. NDCG @K
    ax5 = plt.subplot(3, 4, 5)
    for k in [5, 10, 20]:
        if f'NDCG@{k}' in history and history[f'NDCG@{k}']:
            plt.plot(history['eval_epochs'], history[f'NDCG@{k}'],
                     marker='D', linewidth=2, label=f'NDCG@{k}', markersize=4)
    plt.title('NDCG @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('NDCG')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 6. MAP @K
    ax6 = plt.subplot(3, 4, 6)
    for k in [5, 10, 20]:
        if f'MAP@{k}' in history and history[f'MAP@{k}']:
            plt.plot(history['eval_epochs'], history[f'MAP@{k}'],
                     marker='*', linewidth=2, label=f'MAP@{k}', markersize=4)
    plt.title('MAP @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('MAP')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 7. AUC
    ax7 = plt.subplot(3, 4, 7)
    if 'AUC' in history and history['AUC']:
        plt.plot(history['eval_epochs'], history['AUC'],
                 'purple', marker='*', linewidth=3, label='AUC', markersize=6)
        plt.title('AUC (Area Under Curve)', fontsize=12, fontweight='bold')
        plt.xlabel('Epoch')
        plt.ylabel('AUC')
        plt.legend()
        plt.grid(True, alpha=0.3)

    # 8. Learning Rate Schedule - 안전한 플로팅
    ax8 = plt.subplot(3, 4, 8)
    if history['learning_rates'] and history['eval_epochs']:
        # 길이 확인 및 조정
        lr_length = len(history['learning_rates'])
        eval_length = len(history['eval_epochs'])

        if lr_length == eval_length:
            plt.plot(history['eval_epochs'], history['learning_rates'],
                     'orange', marker='v', linewidth=2, markersize=4)
        elif lr_length < eval_length:
            # learning_rates가 더 짧으면 마지막 값들만 사용
            plt.plot(history['eval_epochs'][-lr_length:], history['learning_rates'],
                     'orange', marker='v', linewidth=2, markersize=4)
        else:
            # learning_rates가 더 길면 처음 eval_length만큼만 사용
            plt.plot(history['eval_epochs'], history['learning_rates'][:eval_length],
                     'orange', marker='v', linewidth=2, markersize=4)

        plt.title('Learning Rate Schedule', fontsize=12, fontweight='bold')
        plt.xlabel('Epoch')
        plt.ylabel('Learning Rate')
        plt.yscale('log')
        plt.grid(True, alpha=0.3)

    # 9. 성능 비교 (마지막 값들)
    ax9 = plt.subplot(3, 4, 9)
    if history['eval_epochs']:
        metrics_names = ['HR@5', 'HR@10', 'HR@20', 'Precision@10', 'Recall@10', 'NDCG@10', 'MAP@10']
        values = []
        for metric in metrics_names:
            if metric in history and history[metric]:
                values.append(history[metric][-1])
            else:
                values.append(0)

        bars = plt.bar(metrics_names, values,
                       color=['skyblue', 'lightgreen', 'lightcoral', 'gold', 'plum', 'lightblue', 'orange'])
        plt.title('Final Performance Metrics', fontsize=12, fontweight='bold')
        plt.ylabel('Score')
        plt.xticks(rotation=45)
        plt.ylim(0, 1)

        # 값 표시
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                     f'{value:.3f}', ha='center', va='bottom', fontsize=8)

    # 10. Precision vs Recall @10
    ax10 = plt.subplot(3, 4, 10)
    if history['eval_epochs'] and len(history['eval_epochs']) > 1:
        if 'Precision@10' in history and history['Precision@10'] and 'Recall@10' in history and history['Recall@10']:
            plt.scatter(history['Recall@10'], history['Precision@10'], alpha=0.6, s=50, c='red')
            plt.xlabel('Recall@10')
            plt.ylabel('Precision@10')
            plt.title('Precision@10 vs Recall@10', fontsize=12, fontweight='bold')
            plt.grid(True, alpha=0.3)

    # 11. HR@10 vs NDCG@10
    ax11 = plt.subplot(3, 4, 11)
    if history['eval_epochs'] and len(history['eval_epochs']) > 1:
        if 'HR@10' in history and history['HR@10'] and 'NDCG@10' in history and history['NDCG@10']:
            plt.scatter(history['NDCG@10'], history['HR@10'], alpha=0.6, s=50, c='green')
            plt.xlabel('NDCG@10')
            plt.ylabel('HR@10')
            plt.title('HR@10 vs NDCG@10', fontsize=12, fontweight='bold')
            plt.grid(True, alpha=0.3)

    # 12. 학습 진행률 요약
    ax12 = plt.subplot(3, 4, 12)
    summary_text = f"""
    Total Epochs: {len(history['epochs'])}
    Best HR@10: {max(history['HR@10']) if history['HR@10'] else 'N/A':.4f}
    Best NDCG@10: {max(history['NDCG@10']) if history['NDCG@10'] else 'N/A':.4f}
    Best Precision@10: {max(history['Precision@10']) if history['Precision@10'] else 'N/A':.4f}
    Final Loss: {history['train_loss'][-1] if history['train_loss'] else 'N/A':.4f}
    """
    plt.text(0.1, 0.5, summary_text, transform=ax12.transAxes, fontsize=10,
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
    plt.title('Training Summary', fontsize=12, fontweight='bold')
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"시각화 결과 저장 완료: {save_path}")
