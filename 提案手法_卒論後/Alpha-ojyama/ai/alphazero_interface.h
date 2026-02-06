#pragma once
#include "../core/core.h"
#include <cstdlib>
#include <fstream>
#include <sstream>

namespace alphazero
{

/**
 * AlphaGo ZeroのPythonスクリプトを呼び出してAI推論
 */
class AlphaZeroPlayer {
private:
    std::string python_script;
    bool model_available;
    
public:
    AlphaZeroPlayer(const std::string& script = "../AlphaGo-Zero-master/inference_cpp.py")
        : python_script(script), model_available(false)
    {
        // モデルファイルの存在確認
        std:: ifstream model_file("../AlphaGo-Zero-master/puyo_model_cpp.pth");
        model_available = model_file.good();
        model_file.close();
        
        if (model_available) {
            printf("✅ AlphaZero モデル検出\n");
        } else {
            printf("⚠️ AlphaZeroモデル未検出\n");
        }
    }
    
    /**
     * AlphaZeroで行動選択
     */
    move::Placement choose_action(const Field& field, const cell::Pair& pair) {
        if (!model_available) {
            // フォールバック:  中央に縦置き
            return { 2, direction::Type::UP };
        }
        
        // 1. 盤面をファイル出力
        export_field(field, "temp_state.txt");
        
        // 2. Pythonスクリプト呼び出し
        std:: string command = "python " + python_script + " temp_state.txt temp_action.txt";
        int ret = system(command.c_str());
        
        if (ret != 0) {
            printf("[WARN] Python呼び出し失敗\n");
            return { 2, direction::Type::UP };
        }
        
        // 3. 結果読み込み
        return import_action("temp_action.txt");
    }
    
    bool is_available() const {
        return model_available;
    }
    
private:
    void export_field(const Field& field, const std:: string& filename) {
        std::ofstream file(filename);
        for (i8 y = 13; y >= 0; --y) {
            for (i8 x = 0; x < 6; ++x) {
                int val = cell_to_int(field.get_cell(x, y));
                file << val;
                if (x < 5) file << ",";
            }
            file << "\n";
        }
        file.close();
    }
    
    move::Placement import_action(const std::string& filename) {
        std::ifstream file(filename);
        std::string line;
        std::getline(file, line);
        file.close();
        
        size_t comma = line.find(',');
        int x = std::stoi(line.substr(0, comma));
        int r = std::stoi(line.substr(comma + 1));
        
        return { static_cast<i8>(x), static_cast<direction::Type>(r) };
    }
    
    int cell_to_int(cell::Type cell) {
        switch (cell) {
            case cell::Type::NONE:     return 0;
            case cell::Type::RED:     return 1;
            case cell::Type::GREEN:   return 2;
            case cell::Type::BLUE:    return 3;
            case cell::Type::YELLOW:   return 4;
            case cell::Type::GARBAGE: return 6;
            default:                  return 0;
        }
    }
};

}  // namespace alphazero