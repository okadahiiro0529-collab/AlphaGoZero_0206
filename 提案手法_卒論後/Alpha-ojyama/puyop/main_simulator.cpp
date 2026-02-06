#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include "../core/core.h"
#include "../core/field.h"
#include "../core/move.h"
#include "../core/chain.h"

/**
 * puyop_simulator.exe
 * 
 * シンプル版（おじゃまぷよはPython側で管理）
 */

static int cell_type_to_int(cell:: Type t) {
    switch (t) {
    case cell::Type::NONE:    return 0;
    case cell::Type::RED:     return 1;
    case cell::Type::GREEN:   return 2;
    case cell::Type::BLUE:    return 3;
    case cell::Type::YELLOW:  return 4;
    case cell::Type::GARBAGE: return 6;
    default:                  return 0;
    }
}

static cell:: Type int_to_cell_type(int val) {
    switch (val) {
    case 0: return cell::Type::NONE;
    case 1: return cell::Type::RED;
    case 2: return cell::Type::GREEN;
    case 3: return cell::Type::BLUE;
    case 4: return cell::Type::YELLOW;
    case 6: return cell::Type::GARBAGE;
    default:   return cell::Type::NONE;
    }
}

Field load_field(const std::string& filename) {
    std::ifstream file(filename);
    if (!file) {
        std::cerr << "load_field: failed to open " << filename << std::endl;
    }
    Field field;

    for (int y = 0; y < 14; ++y) {
        std::string line;
        if (!std::getline(file, line)) {
            std::cerr << "load_field: failed to read line " << y << " from " << filename << std::endl;
            break;
        }
        std::stringstream ss(line);

        for (int x = 0; x < 6; ++x) {
            int val;
            char comma;
            ss >> val;
            if (x < 5) ss >> comma;

            cell::Type type = int_to_cell_type(val);
            if (type != cell::Type::NONE) {
                field.drop_puyo(static_cast<i8>(x), type);
            }
        }
    }
    return field;
}

void save_field(const Field& field, const std::string& filename) {
    std::ofstream file(filename);

    for (int y = 0; y < 14; ++y) {
        for (int x = 0; x < 6; ++x) {
            file << cell_type_to_int(field.get_cell(static_cast<i8>(x), static_cast<i8>(y)));
            if (x < 5) file << ",";
        }
        file << "\n";
    }
}

int main(int argc, char* argv[]) {
    if (argc < 8) {
        std::cerr << "Usage: " << argv[0] 
                  << " <input_field> <x> <rotation> <color1> <color2> <output_field> <output_result>\n";
        return 1;
    }

    std::string input_field_file = argv[1];
    int x = std::stoi(argv[2]);
    int r = std::stoi(argv[3]);
    int c1 = std::stoi(argv[4]);
    int c2 = std::stoi(argv[5]);
    std::string output_field_file = argv[6];
    std::string output_result_file = argv[7];

    std::cerr << "[DEBUG][C++] params: x=" << x << " r=" << r << " c1=" << c1 << " c2=" << c2 << std::endl;

    Field field = load_field(input_field_file);

    auto dir = static_cast<direction:: Type>(r);
    cell:: Pair pair = {int_to_cell_type(c1), int_to_cell_type(c2)};

    // Fieldの中心列高さをdrop_pair前後で比較して異常を検知
    int heights_before[6];
    for (int i = 0; i < 6; ++i) heights_before[i] = field.get_height(i);
    
    // ペアを配置 ― ここで失敗検知
    field.drop_pair(static_cast<i8>(x), dir, pair);

    // drop_pair後の各列高さ
    int heights_after[6];
    for (int i = 0; i < 6; ++i) heights_after[i] = field.get_height(i);

    // 差分をprint
    std::cerr << "[DEBUG][C++] drop_pair: ";
    for (int i = 0; i < 6; ++i) std::cerr << heights_before[i] << "->" << heights_after[i] << " ";
    std::cerr << "(diff: ";
    for (int i = 0; i < 6; ++i) std::cerr << (heights_after[i] - heights_before[i]) << " ";
    std::cerr << ")" << std::endl;

    // 全列で高さ変化が0の場合は異常アクション
    bool any_change = false;
    for (int i = 0; i < 6; ++i) if (heights_after[i] != heights_before[i]) any_change = true;
    if (!any_change) {
        std::cerr << "[ERROR][C++] drop_pair did not change the board at all! x=" << x << ", r=" << r << ", c1=" << c1 << ", c2=" << c2 << std::endl;
    }

    // 連鎖計算
    auto mask = field.pop();
    auto chain_result = chain::get_score(mask);

    // ゲームオーバー判定
    bool game_over = (field.get_height_max() > 12);

    // 結果を保存
    save_field(field, output_field_file);

    std::ofstream result_file(output_result_file);
    result_file << chain_result.score << "\n";
    result_file << chain_result.count << "\n";
    result_file << (game_over ? 1 :  0) << "\n";

    return 0;
}