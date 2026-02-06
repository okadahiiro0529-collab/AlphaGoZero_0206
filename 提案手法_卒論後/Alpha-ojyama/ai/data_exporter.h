#pragma once
#include "../core/core.h"
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <cstdio>   // ← 追加
#ifdef _WIN32
    #include <direct.h>   // ← 追加（_getcwd用）
    #define getcwd _getcwd
#else
    #include <unistd.h>   // ← 追加（getcwd用）
#endif

namespace data_exporter
{

/**
 * 1手分のゲームデータ
 */
struct GameStep {
    std::vector<std::vector<int>> board;  // 14×6の盤面
    std::vector<int> valid_actions;        // 有効な行動リスト
    int chosen_action;                     // 選択した行動
    int chain_score;                       // 連鎖スコア
    int chain_length;                      // 連鎖数
    float reward;                          // 報酬
    std::string replay_url;                // リプレイURL ← 追加
};

/**
 * ゲームデータをCSV形式で出力するクラス
 */
class DataExporter {
private:
    std::vector<GameStep> game_steps;
    std::string output_dir;
    
public:
    DataExporter(const std::string& dir = "../training_data/") 
        : output_dir(dir) 
    {
        std::string mkdir_cmd;
        #if defined(_WIN32) || defined(__MINGW32__) || defined(__MINGW64__)
            // Windows/MINGW用
            mkdir_cmd = "if not exist \"" + dir + "\" mkdir \"" + dir + "\" 2>nul";
        #else
            // Linux/Mac用
            mkdir_cmd = "mkdir -p \"" + dir + "\" 2>/dev/null";
        #endif
        
        int ret = system(mkdir_cmd.c_str());
        
        // デバッグ出力
        printf("[DataExporter] Directory:  %s (ret=%d)\n", dir.c_str(), ret);
    }
    
    /**
     * 現在の盤面とAIの選択を記録
     */
    void record_step(const Field & field,
                    const avec<move::Placement, 22>& valid_moves,
                    const move::Placement& chosen_move,
                    int chain_score,
                    int chain_length,
                    float reward = 0.0f,
                    const std::string& replay_url = "") {
        
        GameStep step;
        
        // 盤面をエンコード
        step.board.resize(14);
        for (int y = 0; y < 14; ++y) {
            step.board[y].resize(6);
            for (int x = 0; x < 6; ++x) {
                step.board[y][x] = cell_to_int(field.get_cell(static_cast<i8>(x), static_cast<i8>(13 - y)));
            }
        }
        
        // 有効な行動をエンコード
        step.valid_actions.clear();
        int num_valid = valid_moves.get_size();  // ← avec::get_size()を使用
        for (int i = 0; i < num_valid; ++i) {
            step.valid_actions.push_back(placement_to_action_id(valid_moves[i]));
        }
        
        // 選択した行動
        step.chosen_action = placement_to_action_id(chosen_move);
        
        // 連鎖情報と報酬
        step.chain_score = chain_score;
        step.chain_length = chain_length;
        step.reward = reward;
        
        game_steps.push_back(step);
    }
    
    /**
    * 収集したデータをCSVファイルに保存
    */
    void save_to_file(int seed, int total_score, int max_chain, const std::string& replay_url = "") {
        std::string filename = output_dir + "game_" + std::to_string(seed) + ".csv";
        
        // デバッグ出力
        printf("[DEBUG] Attempting to save to: %s\n", filename.c_str());
        printf("[DEBUG] Number of steps to save: %zu\n", game_steps.size());

        // ===== 絶対パスを表示 ===== ← 追加
        char current_dir[1024];
        #ifdef _WIN32
            _getcwd(current_dir, sizeof(current_dir));
        #else
            getcwd(current_dir, sizeof(current_dir));
        #endif
        printf("[DEBUG] Current working directory: %s\n", current_dir);
        
        char abs_path[2048];
        snprintf(abs_path, sizeof(abs_path), "%s/%s", current_dir, filename.c_str());
        printf("[DEBUG] Absolute path: %s\n", abs_path);
        // ==========================
        
        // ファイルが空の場合は警告
        if (game_steps.empty()) {
            printf("[WARN] No data to save!  game_steps is empty.\n");
            return;
        }
        
        std::ofstream file(filename);
        
        // ファイルが開けたか確認
        if (!file.is_open()) {
            printf("[ERROR] Failed to open file: %s\n", filename.c_str());
            printf("[ERROR] Check if directory exists and has write permission\n");
            return;
        }
        
        printf("[DEBUG] File opened successfully\n");
        
        // ヘッダー
        file << "step,board,valid_actions,chosen_action,chain_score,chain_length,reward,replay_url\n";
        
        // データ書き込み
        for (size_t i = 0; i < game_steps.size(); ++i) {
            const auto & step = game_steps[i];
            
            file << i << ",";
            
            // 盤面（フラット化）
            file << "\"";
            for (int y = 0; y < 14; ++y) {
                for (int x = 0; x < 6; ++x) {
                    file << step.board[y][x];
                    if (x < 5) file << " ";
                }
                if (y < 13) file << ";";
            }
            file << "\",";
            
            // 有効な行動
            file << "\"";
            for (size_t j = 0; j < step.valid_actions.size(); ++j) {
                file << step.valid_actions[j];
                if (j < step.valid_actions.size() - 1) file << " ";
            }
            file << "\",";
            
            // 選択した行動
            file << step.chosen_action << ",";
            
            // 連鎖情報
            file << step.chain_score << ",";
            file << step.chain_length << "\n";

            // 報酬 ← 追加
            file << step.reward << "\n";

            // リプレイURL（最終手のみ）
            if (i == game_steps.size() - 1) {
                file << replay_url;
            }
            file << "\n";
            
            // 進捗表示（10ステップごと）
            if ((i + 1) % 10 == 0) {
                printf("[DEBUG] Written %zu/%zu steps\n", i + 1, game_steps.size());
            }
        }
        
        file.close();

        printf("Training data saved:  %s (URL: %s)\n", filename.c_str(), replay_url.c_str());
        
        // ファイルサイズ確認
        std::ifstream check_file(filename, std::ios::binary | std::ios::ate);
        if (check_file.is_open()) {
            std:: streamsize file_size = check_file.tellg();
            check_file.close();
            printf("Training data saved: %s (%zu steps, %ld bytes, score=%d, max_chain=%d)\n", 
                   filename.c_str(), game_steps.size(), (long)file_size, total_score, max_chain);
        } else {
            printf("[ERROR] File was written but cannot be read back:  %s\n", filename.c_str());
        }
    }
    
    void clear() {
        game_steps.clear();
    }
    
private:
    int cell_to_int(cell:: Type cell) const {
        switch (cell) {
            case cell::Type::NONE:      return 0;
            case cell::Type::RED:      return 1;
            case cell::Type::GREEN:    return 2;
            case cell::Type::BLUE:      return 3;
            case cell::Type::YELLOW:   return 4;
            case cell::Type::GARBAGE:  return 6;
            default:                   return 0;
        }
    }
    
    /**
     * move::Placementを行動ID（0-23）に変換
     * 形式: action_id = x + direction * 6
     */
    int placement_to_action_id(const move::Placement& p) const {
        int dir_id = 0;
        switch (p.r) {
            case direction::Type::UP:    dir_id = 0; break;
            case direction::Type::RIGHT: dir_id = 1; break;
            case direction::Type::DOWN:  dir_id = 2; break;
            case direction::Type::LEFT:  dir_id = 3; break;
        }
        return p.x + dir_id * 6;
    }
};

}  // namespace data_exporter