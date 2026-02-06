"""
Solver（モンテカルロ + 最終ボーナス + 早期ゲームオーバーペナルティ・真手数カウント対応版）
"""
import numpy as np
from mcts import MCTS
from puyopuyo_env_cpp import PuyoPuyoGame
from puyop_url_encoder import PuyopURLEncoder

class Solver:
    def __init__(self, game, net, num_sims=50, temp_threshold=10):
        self.game = game
        self.net = net
        self.num_sims = num_sims
        self.temp_threshold = temp_threshold
    
    def execute_episode(self, nnet):
        examples = []
        mcts = MCTS(game=self.game, net=nnet, num_sims=self.num_sims)
        
        state = self.game.reset()
        url_encoder = PuyopURLEncoder()
        url_encoder.reset()
        current_pair = self._generate_random_pair()
        
        print(f"自己対戦開始...", flush=True)
        
        # カウント変数
        moves_placed = 0             # ぷよ設置回数
        ojama_drop_count = 0         # おじゃま“降った”回数
        true_step_count = 0          # 実際の総手数（設置+おじゃま回数）
        
        num_moves = 0                # ぷよ設置分としての古い手数（このまま残してもOK）
        total_score = 0
        chain_events = []
        
        immediate_rewards = []
        last_garbage_cols = None

        temperature = 1

        while True:
            # 1. MCTS探索
            for i in range(self.num_sims):
                mcts.search(state.copy())
            
            if num_moves > self.temp_threshold:
                temperature = 0
            else:
                temperature = 1
            
            pi = mcts.get_action_probabilities(state, t=temperature)
            
            valid = self.game.get_valid_moves(state)
            pi = pi * valid  # 有効手以外は確率0
            if np.sum(pi) == 0:
                # もしpi全部0のときは有効手一様
                pi = valid.astype(float) / np.sum(valid)
            else:
                pi = pi / np.sum(pi)
            
            action = np.random.choice(pi.size, p=pi)
            x = action % 6
            rotation = action // 6

            # ここで「使うペアを保存」
            pair_to_use = current_pair

            board_before = state.copy()
            
            # 2. next_stateで盤面・score等取得
            state, _, score, chains, garbage_columns = self.game.next_state(
                state, action=action, current_pair=pair_to_use, is_simulation=False
            )

            board_after = state

            # ぷよの新設置セルを特定
            placed_positions = []
            for y in range(self.game.board_height):
                for x_ in range(self.game.board_width):
                    if board_before[y, x_] == 0 and board_after[y, x_] != 0 and board_after[y, x_] < 6:  # ゴ��(6)除外
                        placed_positions.append((x_, y))

            # 3. ぷよ設置分の手数をインクリメント・URL記録
            url_encoder.add_move(x, rotation, pair_to_use[0], pair_to_use[1])
            moves_placed += 1
            true_step_count += 1
            num_moves += 1  # 本来は非推奨だが古い行に残してもOK

            # 4. おじゃま降下分の手数・URL登録
            if len(garbage_columns) > 0:
                url_encoder.add_garbage_columns(garbage_columns)
                ojama_drop_count += 1
                true_step_count += 1  # おじゃま降下分の手数もカウントアップ

            # 5. last_action系情報を必ず盤面確定直後に更新
            last_action_col = x
            last_action_row = self.game._get_column_height(state, x) - 1
            last_garbage_cols = garbage_columns.copy() if len(garbage_columns) > 0 else []

            # 6. ペナルティ判定・表示（必ずlast_action更新後で！）
            immediate_penalty = 0.0
            reward_tuple_penalty = self.game.reward(
                state,
                last_garbage_cols=last_garbage_cols,
                placed_positions=placed_positions  # ←追加！
            )

            is_gameover_penalty = reward_tuple_penalty[0] == -1
            is_self_over_penalty = reward_tuple_penalty[1]
            is_ojama_over_penalty = reward_tuple_penalty[2]
            move_count_penalty = reward_tuple_penalty[3]

            if is_gameover_penalty and true_step_count <= 100:
                penalty_step_str = f"{true_step_count}手目"
                pen_base = 0
                # 50手未満の死亡なら大ペナルティ
                if true_step_count < 50:
                    pen_base = -1000 + (true_step_count / 50) * 1000  # 0 ～ -400スケール
                    if is_self_over_penalty:
                        pen_base += -750
                        print(f'自分でゲームオーバー（{penalty_step_str}）: penalty={pen_base}')
                    elif is_ojama_over_penalty:
                        print(f'おじゃまぷよでゲームオーバー（{penalty_step_str}）: penalty={pen_base}')
                    immediate_penalty += pen_base
                # 50手以降は自爆のみペナルティ
                elif is_self_over_penalty:
                    pen_base = -500  # 例：自爆の場合は-150（必要に応じて変更）
                    print(f'自分でゲームオーバー（{penalty_step_str}）: penalty={pen_base}')
                    immediate_penalty += pen_base
                # 50手以降かつ“自爆でない”ならペナルティ0（何も足さない）

            # 7. 報酬計算、symmetries追加
            step_reward = self._calculate_step_reward(score, chains, garbage_columns)
            step_reward += immediate_penalty
            symmetries = self.game.get_symmetries(state, pi)

            for sym_board, sym_pi in symmetries:
                examples.append((sym_board, sym_pi, 0))
                immediate_rewards.append(step_reward)  # ←この場所で同時追加！

            # 8. ゲーム終了判定（ここはlast_action更新・報酬計算後で判定する！）
            reward_tuple = self.game.reward(state,
                                            last_garbage_cols=last_garbage_cols,
                                            placed_positions=placed_positions)
            is_gameover = reward_tuple[0] == -1
            is_self_over = reward_tuple[1]
            is_ojama_over = reward_tuple[2]
            # ★本来の手数: ぷよ設置回数 + おじゃま“降った”回数
            # ここで true_step_count を使う

            if is_gameover:
                final_bonus = self._calculate_final_bonus(true_step_count, total_score, chain_events)
                chain_str = self._format_chain_events(chain_events)
                url = url_encoder.generate_url()
                print(f"エピソード終了（{true_step_count}手、{chain_str}、スコア{total_score}、おじゃま{ojama_drop_count}回）:   最終ボーナス={final_bonus:.3f}", flush=True)
                print(f"  URL: {url}", flush=True)
                returns = self._calculate_returns_with_bonus(immediate_rewards, final_bonus, gamma=0.99)
                # ⭐ここでepisode_resultの定義を必ず入れる！
                episode_result = {
                    "score": total_score,
                    "chain_events": chain_events.copy(),
                    "moves": true_step_count,
                    "max_chain": max(chain_events) if chain_events else 0,
                    "avg_chain": np.mean(chain_events) if chain_events else 0.0
                }
                if len(returns) != len(examples):
                    print(f"[WARNING] returns({len(returns)}) != examples({len(examples)})", flush=True)
                    avg_return = np.mean(returns) if len(returns) > 0 else 0.0
                    return [(s, pi, avg_return) for s, pi, _ in examples]
                return [(examples[i][0], examples[i][1], returns[i]) for i in range(len(examples))], episode_result
            
            # 100“手”で強制終了: 総合的な手数でカウント
            if true_step_count >= 100:
                final_bonus = self._calculate_final_bonus(true_step_count, total_score, chain_events)
                chain_str = self._format_chain_events(chain_events)
                url = url_encoder.generate_url()
                print(f"最大手数到達（{true_step_count}手、{chain_str}、スコア{total_score}、おじゃま{ojama_drop_count}回）: 最終ボーナス={final_bonus:.3f}", flush=True)
                print(f"  URL: {url}", flush=True)
                returns = self._calculate_returns_with_bonus(immediate_rewards, final_bonus, gamma=0.99)
                episode_result = {
                    "score": total_score,
                    "chain_events": chain_events.copy(),
                    "moves": true_step_count,
                    "max_chain": max(chain_events) if chain_events else 0,
                    "avg_chain": np.mean(chain_events) if chain_events else 0.0
                }
                if len(returns) != len(examples):
                    print(f"[WARNING] returns({len(returns)}) != examples({len(examples)})", flush=True)
                    avg_return = np.mean(returns) if len(returns) > 0 else 0.0
                    return [(s, pi, avg_return) for s, pi, _ in examples]
                return [(examples[i][0], examples[i][1], returns[i]) for i in range(len(examples))], episode_result

            # 9. チェインイベントやスコア、ペアなど
            if chains > 0:
                chain_events.append(chains)
            
            total_score += score
            current_pair = self._generate_random_pair()
            # num_moves += 1   ← 既に上部でインクリメント済み

        
    def _calculate_step_reward(self, score, chains, garbage_columns):
        chain_bonus = 0
        if chains >= 3:
            chain_bonus = 250 * (chains-2)  # 例えば3連鎖で+200, 4連鎖で+400...
        survival_bonus = 5
        return score + chain_bonus + survival_bonus
    
    def _calculate_final_bonus(self, moves, score, chain_events):
        survival_bonus = moves * 2.0
        score_bonus = score * 0.05
        if len(chain_events) > 0:
            avg_chain = np.mean(chain_events)
            max_chain = max(chain_events)
            chain_bonus = 10.0 * (avg_chain ** 2) + 30.0 * (max_chain ** 2)
        else:
            chain_bonus = 0.0
        total_bonus = survival_bonus + score_bonus + chain_bonus
        return total_bonus
    
    def _calculate_returns_with_bonus(self, immediate_rewards, final_bonus, gamma=0.99):
        if len(immediate_rewards) == 0:
            return []
        returns = []
        G = final_bonus
        for r in reversed(immediate_rewards):
            G = r + gamma * G
            returns.insert(0, G)
        returns = np.array(returns)
        mean = np.mean(returns)
        std = np.std(returns)
        if std > 1e-8:
            normalized = (returns - mean) / std
        else:
            normalized = returns - mean
        normalized = np.tanh(normalized * 0.5)
        return normalized.tolist()
    
    def _format_chain_events(self, chain_events):
        if len(chain_events) == 0:
            return "連鎖なし"
        total = sum(chain_events)
        if len(chain_events) <= 5:
            chain_list_str = ', '.join(map(str, chain_events))
            return f"[{chain_list_str}]連鎖 (計{total})"
        else:
            first_three = ', '.join(map(str, chain_events[:3]))
            remaining = len(chain_events) - 3
            return f"[{first_three}, ... +{remaining}個]連鎖 (計{total})"
    
    def _generate_random_pair(self):
        color1 = np.random.randint(1, 5)
        color2 = np.random.randint(1, 5)
        return (color1, color2)
    
    def train(self, examples, batch_size=32, epochs=10):
        import torch
        import torch.optim as optim
        
        optimizer = optim.Adam(self.net.parameters(), lr=0.0005)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.net = self.net.to(device)
        
        print(f"学習開始（データ数:  {len(examples)}）", flush=True)
        
        for epoch in range(epochs):
            np.random.shuffle(examples)
            total_loss = 0
            batches = 0
            for i in range(0, len(examples), batch_size):
                batch = examples[i:i+batch_size]
                states = torch.FloatTensor(np.array([s for s, _, _ in batch])).unsqueeze(1).to(device)
                target_pis = torch.FloatTensor(np.array([pi for _, pi, _ in batch])).to(device)
                target_vs = torch.FloatTensor(np.array([[z] for _, _, z in batch])).to(device)
                pred_pis, pred_vs = self.net(states)
                loss_pi = -torch.sum(target_pis * torch.log(pred_pis + 1e-8)) / target_pis.size(0)
                loss_v = torch.sum((target_vs - pred_vs) ** 2) / target_vs.size(0)
                loss = loss_pi + loss_v
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                batches += 1
            avg_loss = total_loss / batches
            print(f"    Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}", flush=True)
        print(f"学習完了", flush=True)