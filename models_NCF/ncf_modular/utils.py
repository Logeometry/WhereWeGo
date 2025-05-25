# utils.py
# 유틸리티 함수 모듈

import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def save_checkpoint(model, optimizer, epoch, path):
    """모델 체크포인트 저장"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, path)

def visualize_training_extended(history, save_path):
    """
    10개 서브플롯으로 구성된 종합 학습 시각화 생성
    
    Args:
        history (dict): 메트릭과 손실을 포함하는 학습 이력
        save_path (str): 시각화를 저장할 경로
    """
    plt.style.use('default')
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Training & Validation Loss
    ax1 = plt.subplot(3, 4, 1)
    plt.plot(history['epochs'], history['train_loss'], 'b-', linewidth=2, alpha=0.8, label='Train Loss')
    if 'val_loss' in history and history['val_loss']:
        plt.plot(history['epochs'], history['val_loss'], 'r-', linewidth=2, alpha=0.8, label='Val Loss')
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
    
    # 3. Recall @K
    ax3 = plt.subplot(3, 4, 3)
    for k in [5, 10, 20]:
        if f'Recall@{k}' in history and history[f'Recall@{k}']:
            plt.plot(history['eval_epochs'], history[f'Recall@{k}'], 
                    marker='s', linewidth=2, label=f'Recall@{k}', markersize=4)
    plt.title('Recall @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Recall')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 4. NDCG @K
    ax4 = plt.subplot(3, 4, 4)
    for k in [5, 10, 20]:
        if f'NDCG@{k}' in history and history[f'NDCG@{k}']:
            plt.plot(history['eval_epochs'], history[f'NDCG@{k}'], 
                    marker='^', linewidth=2, label=f'NDCG@{k}', markersize=4)
    plt.title('NDCG @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('NDCG')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 5. MAP @K
    ax5 = plt.subplot(3, 4, 5)
    for k in [5, 10, 20]:
        if f'MAP@{k}' in history and history[f'MAP@{k}']:
            plt.plot(history['eval_epochs'], history[f'MAP@{k}'], 
                    marker='D', linewidth=2, label=f'MAP@{k}', markersize=4)
    plt.title('MAP @K', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('MAP')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 6. AUC
    ax6 = plt.subplot(3, 4, 6)
    if 'AUC' in history and history['AUC']:
        plt.plot(history['eval_epochs'], history['AUC'], 
                'purple', marker='*', linewidth=3, label='AUC', markersize=6)
        plt.title('AUC (Area Under Curve)', fontsize=12, fontweight='bold')
        plt.xlabel('Epoch')
        plt.ylabel('AUC')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # 7. HR@10 vs Normalized Loss
    ax7 = plt.subplot(3, 4, 7)
    if history['HR@10'] and history['train_loss']:
        normalized_loss = np.array(history['train_loss']) / max(history['train_loss'])
        plt.plot(history['epochs'], normalized_loss, 'r-', alpha=0.7, label='Normalized Loss')
        
        if len(history['eval_epochs']) > 0:
            plt.plot(history['eval_epochs'], history['HR@10'], 'g-', marker='o', 
                    label='HR@10', linewidth=2, markersize=4)
        
        plt.title('Loss vs Performance', fontsize=12, fontweight='bold')
        plt.xlabel('Epoch')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # 8. Learning Rate Schedule
    ax8 = plt.subplot(3, 4, 8)
    if history['learning_rates']:
        plt.plot(history['eval_epochs'], history['learning_rates'], 
                'orange', marker='v', linewidth=2, markersize=4)
        plt.title('Learning Rate Schedule', fontsize=12, fontweight='bold')
        plt.xlabel('Epoch')
        plt.ylabel('Learning Rate')
        plt.yscale('log')
        plt.grid(True, alpha=0.3)
    
    # 9. 성능 비교 (마지막 값들)
    ax9 = plt.subplot(3, 4, 9)
    if history['eval_epochs']:
        metrics_names = ['HR@5', 'HR@10', 'HR@20', 'Recall@10', 'NDCG@10', 'MAP@10']
        values = []
        for metric in metrics_names:
            if metric in history and history[metric]:
                values.append(history[metric][-1])
            else:
                values.append(0)
        
        bars = plt.bar(range(len(metrics_names)), values, 
                      color=['skyblue', 'lightgreen', 'lightcoral', 'gold', 'plum', 'lightsalmon'])
        plt.title('Final Performance', fontsize=12, fontweight='bold')
        plt.xticks(range(len(metrics_names)), metrics_names, rotation=45)
        plt.ylabel('Score')
        
        # 값 표시
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{value:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 10. 상세 통계 테이블
    ax10 = plt.subplot(3, 4, (10, 12))
    plt.axis('off')
    
    if history['eval_epochs']:
        # 표 데이터 생성
        table_data = []
        metrics_list = ['HR@5', 'HR@10', 'HR@20', 'Recall@5', 'Recall@10', 'Recall@20', 
                       'NDCG@5', 'NDCG@10', 'NDCG@20', 'MAP@5', 'MAP@10', 'MAP@20', 'AUC']
        
        for metric in metrics_list:
            if metric in history and history[metric]:
                final_val = history[metric][-1]
                max_val = max(history[metric])
                min_val = min(history[metric])
                avg_val = np.mean(history[metric])
                table_data.append([metric, f'{final_val:.4f}', f'{max_val:.4f}', 
                                 f'{min_val:.4f}', f'{avg_val:.4f}'])
        
        # 추가 정보
        total_epochs = max(history['epochs']) if history['epochs'] else 0
        eval_count = len(history['eval_epochs'])
        final_lr = history['learning_rates'][-1] if history['learning_rates'] else 0
        
        table_data.append(['', '', '', '', ''])
        table_data.append(['Total Epochs', str(total_epochs), '', '', ''])
        table_data.append(['Evaluations', str(eval_count), '', '', ''])
        table_data.append(['Final LR', f'{final_lr:.2e}', '', '', ''])
        
        # 표 생성
        table = plt.table(cellText=table_data,
                         colLabels=['Metric', 'Final', 'Max', 'Min', 'Avg'],
                         cellLoc='center',
                         loc='center',
                         bbox=[0, 0, 1, 1])
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.8)
        
        # 헤더 스타일
        for i in range(5):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.title('Training Summary', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.show()
    
    print(f"학습 결과 시각화 저장: {save_path}") 