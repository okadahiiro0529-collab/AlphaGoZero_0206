#include "../core/ctrl.h"
#include "../core/field.h"
#include "../core/player.h"
#include "../core/AI.h"
#include "../core/chain.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>
#include <chrono>

using namespace std;

// 盤面を文字列化（CSV形式）
string field_to_string(const Field& field) {
    ostringstream oss;
    for (i8 y = 13; y >= 0; --y) {
        for (i8 x = 0; x < 6; ++x) {
            int val = 0;
            switch (field.get_cell(x, y)) {
                case cell::Type::RED: val = 1; break;
                case cell::Type::GREEN: val = 2; break;
                case cell::Type:: BLUE: val = 3; break;
                case cell::Type::YELLOW: val = 4; break;
                case cell:: Type::PURPLE: val = 5; break;
                default:  val = 0;
            }
            oss << val;
            if (x < 5) oss << ",";
        }
        if (y > 0) oss << ",";
    }
    return oss.str();
}

// 報酬計算関数
float calculate_reward(int moves, int chain_length, int chain_score, bool game_over) {
    float reward = 0.0f;
    
    // 1.  生存ボーナス（手数に比例）
    reward += moves * 1.0f;
    
    // 2. 連鎖ボーナス（連鎖数に応じて指数的に増加）
    if (chain_length >= 2) {
        reward += chain_length * chain_length * 10.0f;  // 2連鎖=40, 3連鎖=90, 4連鎖=160
    }
    
    // 3. スコアボーナス（獲得スコアの10%）
    reward += chain_score * 0.1f;
    
    // 4. ゲームオーバーペナルティ
    if (game_over && moves < 30) {
        reward -= (30 - moves) * 2.0f;  // 早期終了にペナルティ
    }
    
    return reward;
}

struct GameState {
    string board;
    int action;
    float reward;
    int chain_length;
    int chain_score;
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <seed>" << endl;
        return 1;
    }
    
    u32 seed = stoul(argv[1]);
    srand(seed);
    
    // ゲーム初期化
    Field field;
    vector<cell::Pair> queue(128);
    for (auto& p : queue) {
        p = cell::make_pair();
    }
    
    // AI初期化
    Player player;
    player.field = field;
    
    int placements_done = 0;
    bool game_over = false;
    int total_score = 0;
    int max_chain_length = 0;
    
    // ゲーム履歴を保存
    vector<GameState> game_history;
    
    // ゲームループ
    while (! game_over && placements_done < 100) {
        // 現在の盤面を記録
        string board_str = field_to_string(field);
        
        // AIで次の手を決定
        vector<cell::Pair> tqueue;
        tqueue. push_back(queue[placements_done % 128]);
        tqueue.push_back(queue[(placements_done + 1) % 128]);
        
        player.field = field;
        auto best_move = player. think(tqueue, 2);  // ビームサーチ
        
        // ゲームオーバー判定
        if (field. get_height(2) > 11) {
            game_over = true;
            break;
        }
        
        // 手を実行
        field. drop_pair(best_move. x, best_move.r, tqueue[0]);
        auto mask = field.pop();
        
        // 連鎖情報を取得
        auto chain_info = chain::get_score(mask);
        int chain_length = chain_info. count;
        int chain_score = chain_info.score;
        
        total_score += chain_score;
        
        if (chain_length > max_chain_length) {
            max_chain_length = chain_length;
        }
        
        // 行動IDを計算
        int action_id = best_move.x * 4 + best_move.r;
        
        // ゲーム状態を記録（報酬は後で計算）
        GameState state;
        state.board = board_str;
        state.action = action_id;
        state. chain_length = chain_length;
        state.chain_score = chain_score;
        state.reward = 0.0f;  // 暫定
        
        game_history.push_back(state);
        
        placements_done++;
    }
    
    // ゲーム終了後、全ての手に対して報酬を計算
    for (size_t i = 0; i < game_history.size(); ++i) {
        auto& state = game_history[i];
        
        // 即時報酬（その手での連鎖とスコア）
        float immediate_reward = calculate_reward(
            1,  // 1手あたり
            state.chain_length,
            state.chain_score,
            false
        );
        
        // 最終報酬（ゲーム全体の評価）
        float final_reward = calculate_reward(
            placements_done,
            max_chain_length,
            total_score,
            game_over
        );
        
        // 割引報酬（後の手ほど最終報酬の影響が大きい）
        float gamma = 0.99f;
        float discount = pow(gamma, game_history.size() - i - 1);
        
        state.reward = immediate_reward + discount * final_reward / game_history.size();
    }
    
    // CSVに保存
    string output_dir = "C:/AlphaGo-Zero-master/training_data/";
    string filename = output_dir + "game_" + to_string(seed) + ".csv";
    
    ofstream data_file(filename);
    
    // ヘッダー
    data_file << "board,chosen_action,reward,chain_length,chain_score" << endl;
    
    // データ書き込み
    for (const auto& state : game_history) {
        data_file << state.board << ","
                  << state.action << ","
                  << state.reward << ","
                  << state.chain_length << ","
                  << state.chain_score << endl;
    }
    
    data_file. close();
    
    // サマリー表示
    cout << "seed:  " << seed 
         << ", moves: " << placements_done 
         << ", score: " << total_score
         << ", max_chain:  " << max_chain_length 
         << endl;
    
    return 0;
}