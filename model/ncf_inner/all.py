import os, json, random
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt  # ✅ 시각화 추가

# 설정
SEED = 42
BATCH_SIZE = 512
EPOCHS = 30
LR = 8e-5
ITEM_LR = 2e-5
WEIGHT_DECAY = 5e-5
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 시드 고정
torch.manual_seed(SEED)
random.seed(SEED)
np.random.seed(SEED)

# 데이터 로딩 - 시간대별 필터링 지원
# config에서 파일 경로 가져오기
from .config import CONFIG
import os

# 데이터 파일 경로 구성
data_file_path = os.path.join(CONFIG['data_dir'], CONFIG['interaction_file'])

# 파일이 존재하는지 확인하고 로딩
if os.path.exists(data_file_path):
    with open(data_file_path, "r") as f:
        raw_data = json.load(f)
        triplet_data = raw_data["triplets"]
else:
    # 대체 경로들 시도
    alternative_paths = [
        CONFIG['interaction_file'],  # 현재 디렉토리
        os.path.join('..', CONFIG['interaction_file']),  # 상위 디렉토리
        os.path.join('..', 'data', CONFIG['interaction_file']),  # 상위/data/
        os.path.join('data', CONFIG['interaction_file']),  # data/
    ]

    data_file_path = None
    for path in alternative_paths:
        if os.path.exists(path):
            data_file_path = path
            break

    if data_file_path:
        print(f"데이터 파일을 찾았습니다: {data_file_path}")
        with open(data_file_path, "r") as f:
            raw_data = json.load(f)
            triplet_data = raw_data["triplets"]
    else:
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {CONFIG['interaction_file']}\n"
                                f"시도한 경로들: {[CONFIG['data_dir']] + alternative_paths}")

# triplet 구조 분석
print(f"총 triplets: {len(triplet_data)}")
new_structure_count = sum(1 for t in triplet_data if len(t) == 6)
old_structure_count = sum(1 for t in triplet_data if len(t) == 5)
legacy_structure_count = sum(1 for t in triplet_data if len(t) == 3)
print(f"새로운 구조 (6개 요소, 시간대 포함): {new_structure_count}")
print(f"기존 구조 (5개 요소): {old_structure_count}")
print(f"레거시 구조 (3개 요소): {legacy_structure_count}")

# 사용자, 아이템 매핑
interactions = {}
for triplet in triplet_data:
    if len(triplet) == 6:  # 새로운 구조: [user_id, category_group, activity_level, time_period, pos_item_index, neg_item_index]
        user_id, category_group, activity_level, time_period, pos_item, neg_item = triplet
        uid = str(user_id)
        interactions.setdefault(uid, []).extend([pos_item, neg_item])
    elif len(triplet) == 5:  # 기존 구조: [user_id, category_group, activity_level, pos_item_index, neg_item_index]
        user_id, category_group, activity_level, pos_item, neg_item = triplet
        uid = str(user_id)
        interactions.setdefault(uid, []).extend([pos_item, neg_item])
    elif len(triplet) == 3:  # 레거시 구조: [user_id, pos_item_index, neg_item_index]
        user_id, pos_item, neg_item = triplet
        uid = str(user_id)
        interactions.setdefault(uid, []).extend([pos_item, neg_item])

# 사용자 ID를 숫자 기준으로 정렬하여 연속적인 인덱스 할당
user_ids = sorted(interactions.keys(), key=lambda x: int(x))
user_id_to_idx = {uid: i for i, uid in enumerate(user_ids)}
item_set = set(i for items in interactions.values() for i in items)
item_id_to_idx = {iid: i for i, iid in enumerate(sorted(item_set))}
n_users = len(user_id_to_idx)
n_items = len(item_id_to_idx)

# 사용자 ID 분포 확인
user_ids_int = [int(uid) for uid in user_ids]
print(f"사용자 ID 범위: {min(user_ids_int)} ~ {max(user_ids_int)}")
print(f"고유 사용자 ID: {user_ids_int}")
print(f"실제 사용자 수: {len(user_ids_int)}명")


# 샘플 생성 - 시간대별 필터링 지원
class NCFDataset(Dataset):
    def __init__(self, triplets, negative_ratio=0):
        self.samples = []

        for triplet in triplets:
            if len(triplet) == 6:  # 새로운 구조 (시간대 포함)
                user_id, category_group, activity_level, time_period, pos_item, neg_item = triplet
                uid = str(user_id)
                if uid in user_id_to_idx and pos_item in item_id_to_idx and neg_item in item_id_to_idx:
                    uidx = user_id_to_idx[uid]
                    pos_idx = item_id_to_idx[pos_item]
                    neg_idx = item_id_to_idx[neg_item]

                    # 긍정 샘플
                    self.samples.append((uidx, pos_idx, 1.0, category_group, activity_level, time_period))
                    # 부정 샘플
                    self.samples.append((uidx, neg_idx, 0.0, category_group, activity_level, time_period))

            elif len(triplet) == 5:  # 기존 구조
                user_id, category_group, activity_level, pos_item, neg_item = triplet
                uid = str(user_id)
                if uid in user_id_to_idx and pos_item in item_id_to_idx and neg_item in item_id_to_idx:
                    uidx = user_id_to_idx[uid]
                    pos_idx = item_id_to_idx[pos_item]
                    neg_idx = item_id_to_idx[neg_item]

                    # 긍정 샘플 (기본 시간대: 오후)
                    self.samples.append((uidx, pos_idx, 1.0, category_group, activity_level, 1))
                    # 부정 샘플
                    self.samples.append((uidx, neg_idx, 0.0, category_group, activity_level, 1))

            elif len(triplet) == 3:  # 레거시 구조
                user_id, pos_item, neg_item = triplet
                uid = str(user_id)
                if uid in user_id_to_idx and pos_item in item_id_to_idx and neg_item in item_id_to_idx:
                    uidx = user_id_to_idx[uid]
                    pos_idx = item_id_to_idx[pos_item]
                    neg_idx = item_id_to_idx[neg_item]

                    # 긍정 샘플 (기본값)
                    self.samples.append((uidx, pos_idx, 1.0, "unknown", 1, 1))
                    # 부정 샘플
                    self.samples.append((uidx, neg_idx, 0.0, "unknown", 1, 1))

        random.shuffle(self.samples)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


# 모델 - 시간대별 필터링 지원
class SimpleResidualNCF(nn.Module):
    def __init__(self, n_users, n_items):
        super().__init__()
        self.user_embed = nn.Embedding(n_users, 64)
        self.item_embed = nn.Embedding(n_items, 64)
        self.user_activity = nn.Embedding(n_users, 3)  # 활동성 레벨 임베딩
        self.user_time_period = nn.Embedding(n_users, 3)  # 시간대별 임베딩
        self.category_group_embed = nn.Embedding(8, 16)  # 카테고리 그룹 임베딩

        self.res_block = nn.Sequential(
            nn.Linear(64, 96),
            nn.ReLU(),
            nn.Linear(96, 64)
        )

        # 최종 융합 (64*2 + 3 + 3 + 16 = 150차원)
        self.mlp = nn.Sequential(
            nn.Linear(150, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, users, items, category_groups=None, activity_levels=None, time_periods=None):
        u = self.user_embed(users)
        i = self.item_embed(items)
        res_i = self.res_block(i) + i

        # 활동성 레벨 임베딩
        if activity_levels is not None:
            activity_emb = self.user_activity(users)
        else:
            activity_emb = torch.zeros(users.size(0), 3, device=users.device)

        # 시간대별 임베딩
        if time_periods is not None:
            time_emb = self.user_time_period(users)
        else:
            time_emb = torch.zeros(users.size(0), 3, device=users.device)

        # 카테고리 그룹 임베딩
        if category_groups is not None:
            category_indices = self._get_category_indices(category_groups, users.device)
            category_emb = self.category_group_embed(category_indices)
        else:
            category_emb = torch.zeros(users.size(0), 16, device=users.device)

        x = torch.cat([u, res_i, activity_emb, time_emb, category_emb], dim=-1)

        # 디버깅: 차원 확인
        if x.size(1) != 150:
            print(f"Warning: Expected 150 dimensions, got {x.size(1)}")
            print(
                f"User: {u.size(1)}, Item: {res_i.size(1)}, Activity: {activity_emb.size(1)}, Time: {time_emb.size(1)}, Category: {category_emb.size(1)}")

        return self.mlp(x).squeeze()

    def _get_category_indices(self, category_groups, device):
        """카테고리 그룹명을 인덱스로 변환 - 디바이스 처리 개선"""
        category_mapping = {
            "자연풍경": 0, "예술 감상": 1, "공연관람": 2, "관람및체험": 3,
            "트레킹": 4, "휴양": 5, "테마거리": 6, "자연산림": 7
        }

        indices = []
        for category in category_groups:
            if isinstance(category, str):
                indices.append(category_mapping.get(category, 0))
            else:
                indices.append(0)

        return torch.tensor(indices, dtype=torch.long, device=device)


# 평가 함수: HR@10, Precision@10, NDCG@10
def evaluate(model, triplets, k=10):
    model.eval()
    HR, Precision, NDCG = [], [], []

    # triplet에서 유저별 positive 아이템 수집
    user_positive_items = {}
    for triplet in triplets:
        if len(triplet) >= 3:
            user_id = str(triplet[0])
            if len(triplet) == 6:  # 새로운 구조 (시간대 포함)
                pos_item = triplet[4]
            elif len(triplet) == 5:  # 기존 구조
                pos_item = triplet[3]
            else:  # 레거시 구조
                pos_item = triplet[1]

            if user_id in user_id_to_idx and pos_item in item_id_to_idx:
                user_idx = user_id_to_idx[user_id]
                item_idx = item_id_to_idx[pos_item]

                if user_idx not in user_positive_items:
                    user_positive_items[user_idx] = set()
                user_positive_items[user_idx].add(item_idx)

    with torch.no_grad():
        for user_idx, true_items in user_positive_items.items():
            u_tensor = torch.tensor([user_idx] * n_items).to(DEVICE)
            i_tensor = torch.tensor(list(range(n_items))).to(DEVICE)

            scores = model(u_tensor, i_tensor).cpu().numpy()

            rank = np.argsort(scores)[::-1][:k]
            hits = [1 if i in true_items else 0 for i in rank]

            HR.append(1 if sum(hits) > 0 else 0)

            # Precision@K 계산
            precision = sum(hits) / k
            Precision.append(precision)

            if sum(hits) == 0:
                NDCG.append(0)
            else:
                dcg = sum([1 / np.log2(i + 2) for i, h in enumerate(hits) if h])
                idcg = sum([1 / np.log2(i + 2) for i in range(min(len(true_items), k))])
                NDCG.append(dcg / idcg)

    return np.mean(HR), np.mean(Precision), np.mean(NDCG)


# 데이터 분할
split_ratio = [0.7, 0.2, 0.1]
train, val, test = [], [], []

# 유저별로 triplets 그룹화
user_triplets = {}
for triplet in triplet_data:
    if len(triplet) >= 3:
        user_id = str(triplet[0])
        if user_id not in user_triplets:
            user_triplets[user_id] = []
        user_triplets[user_id].append(triplet)

for user_id, user_triplet_list in user_triplets.items():
    n_train = int(len(user_triplet_list) * split_ratio[0])
    n_val = int(len(user_triplet_list) * split_ratio[1])

    train.extend(user_triplet_list[:n_train])
    val.extend(user_triplet_list[n_train:n_train + n_val])
    test.extend(user_triplet_list[n_train + n_val:])

train_loader = DataLoader(NCFDataset(train), batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(NCFDataset(val), batch_size=BATCH_SIZE)
test_loader = DataLoader(NCFDataset(test), batch_size=BATCH_SIZE)

# 학습 준비
model = SimpleResidualNCF(n_users, n_items).to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
loss_fn = nn.BCEWithLogitsLoss()

# 로그 저장용 리스트
train_loss_list = []
hr10_list = []
ndcg10_list = []

# 학습 루프
for epoch in range(1, EPOCHS + 1):
    model.train()
    total_loss = 0
    for batch in tqdm(train_loader, desc=f"Epoch {epoch}"):
        if len(batch) == 6:  # 새로운 구조 (시간대 포함)
            u, i, y, c, a, t = batch
            u, i, y = u.to(DEVICE), i.to(DEVICE), y.to(DEVICE)
            c, a, t = c.to(DEVICE), a.to(DEVICE), t.to(DEVICE)
            opt.zero_grad()
            pred = model(u, i, c, a, t)
        elif len(batch) == 5:  # 기존 구조
            u, i, y, c, a = batch
            u, i, y = u.to(DEVICE), i.to(DEVICE), y.to(DEVICE)
            c, a = c.to(DEVICE), a.to(DEVICE)
            # 기본 시간대 (오후) 사용
            t = torch.ones_like(a)
            opt.zero_grad()
            pred = model(u, i, c, a, t)
        else:  # 레거시 구조
            u, i, y = batch
            u, i, y = u.to(DEVICE), i.to(DEVICE), y.to(DEVICE)
            opt.zero_grad()
            pred = model(u, i)

        loss = loss_fn(pred, y)
        loss.backward()
        opt.step()
        total_loss += loss.item()

    avg_loss = total_loss / len(train_loader)
    train_loss_list.append(avg_loss)

    # 평가
    hr10, precision10, ndcg10 = evaluate(model, test, k=10)
    hr10_list.append(hr10)
    ndcg10_list.append(ndcg10)

    print(
        f"[Epoch {epoch}] Loss: {avg_loss:.4f} | HR@10: {hr10:.4f} | Precision@10: {precision10:.4f} | NDCG@10: {ndcg10:.4f}")

    # 5번째 에폭에 모델 저장
    if epoch == 9:
        save_path = "../ncf_time_model_epoch_5.pth"
        torch.save(model.state_dict(), save_path)
        print(f"Epoch 5 모델 저장 완료: {save_path}")

# 최종 저장
torch.save(model.state_dict(), "../ncf_time_model.pth")

# 그래프 시각화
epochs = list(range(1, EPOCHS + 1))
plt.figure(figsize=(10, 6))
plt.plot(epochs, train_loss_list, label='Train Loss')
plt.plot(epochs, hr10_list, label='HR@10')
plt.plot(epochs, ndcg10_list, label='NDCG@10')
plt.xlabel('Epoch')
plt.ylabel('Score')
plt.title('Training Loss, HR@10, and NDCG@10 (Time-based Filtering Support)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("ncf_time_training_graph.png")
plt.show()
