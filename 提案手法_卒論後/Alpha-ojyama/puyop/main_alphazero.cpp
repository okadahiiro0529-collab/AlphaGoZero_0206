#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <cstdlib>
#include <ctime>
#include <string>
#include <sstream>
#include <random>
#include <algorithm>
#include <array>
#include <chrono>
#include "../ai/ai.h"
#include "encode.h"

void load_json(beam::eval::Weight& h)
{
    std::ifstream file;
    file.open("config.json");
    json js;
    file >> js;
    file.close();
    from_json(js, h);
}

void save_json()
{
    std::ifstream f("config.json");
    if (f.good()) {
        return;
    }
    f.close();

    std::ofstream o("config.json");
    json js;
    to_json(js, beam::eval::Weight());
    o << std::setw(4) << js << std::endl;
    o.close();
}

struct ScheduledGarbage {
    int due_move;
    int count;
};

static bool has_conflict(const std::vector<ScheduledGarbage>& schedule, int due) {
    for (const auto &s : schedule) {
        if (s.due_move == due) return true;
        if (s.due_move == due - 1) return true;
        if (s.due_move == due + 1) return true;
    }
    return false;
}

static std::array<int,6> get_all_heights(Field& field) {
    std::array<int,6> h;
    for (int x = 0; x < 6; ++x) {
        h[x] = field.get_height(x);
    }
    return h;
}

static int cell_type_to_int(cell::Type t) {
    switch (t) {
    case cell::Type::NONE:     return 0;
    case cell::Type::RED:     return 1;
    case cell::Type::GREEN:   return 2;
    case cell::Type::BLUE:     return 3;
    case cell::Type::YELLOW:  return 4;
    case cell::Type::GARBAGE: return 6;
    default:                   return 0;
    }
}

static void push_control_entry(std::vector<cell:: Pair>& control_queue,
                               std::vector<move::Placement>& control_placements,
                               std::vector<Field>& control_field_snapshots,
                               const Field& current_field,
                               const cell::Pair& pair,
                               const move::Placement& plc)
{
    control_queue. push_back(pair);
    control_placements.push_back(plc);
    control_field_snapshots.push_back(current_field);
}

void export_field_for_python(const Field& field, const std:: string& filename) {
    std::ofstream file(filename);
    for (i8 y = 13; y >= 0; --y) {
        for (i8 x = 0; x < 6; ++x) {
            int val = cell_type_to_int(field.get_cell(x, y));
            file << val;
            if (x < 5) file << ",";
        }
        file << "\n";
    }
    file.close();
}

move::Placement import_action_from_python(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.good()) {
        return { 2, direction::Type::UP };
    }
    
    std::string line;
    std::getline(file, line);
    file.close();
    
    size_t comma = line.find(',');
    if (comma == std::string::npos) {
        return { 2, direction::Type::UP };
    }
    
    int x = std::stoi(line.substr(0, comma));
    int r = std::stoi(line. substr(comma + 1));
    
    return { static_cast<i8>(x), static_cast<direction::Type>(r) };
}

int total_chain_events = 0;
int sum_chain_lengths = 0;
int max_chain_length = 0;
int total_popped_overall = 0;

int main(int argc, char** argv)
{
    using namespace std;

    srand(uint32_t(time(NULL)));
    
    u32 seed = rand() & 0xFFFF;
    seed = rand() & 0xFFFF;

    if (argc == 2) {
        seed = std:: atoi(argv[1]);
    }

    printf("seed: %d\n", seed);

    auto queue = cell::create_queue(seed);
    Field field;

    vector<cell::Pair> control_queue;
    vector<move::Placement> control_placements;
    std::vector<Field> control_field_snapshots;
    std::vector<int> chain_events;
    vector<move::Placement> placements_for_sim;
    vector<ScheduledGarbage> schedule;

    i32 logical = 0;
    i32 placements_done = 0;
    i32 time = 0;
    i32 score = 0;

    // 初期おじゃまスケジュール
    {
        int init_delay = (rand() % 3) + 3;
        int init_gcount = (rand() % 3) + 1;
        int init_due = init_delay;
        if (init_due < 100) {
            schedule.push_back(ScheduledGarbage{ init_due, init_gcount });
        }
    }

    bool stopped_by_game_over = false;

    while (logical < 100) {
        std::vector<ScheduledGarbage> pending_schedules;
        bool did_garbage = false;

        // おじゃま処理
        for (auto it = schedule.begin(); it != schedule.end(); ) {
            if (it->due_move == logical) {
                int gcount = it->count;
                auto heights_before = get_all_heights(field);
                field.drop_garbage_random(gcount);
                auto heights_after = get_all_heights(field);

                int deltas[6];
                for (int x = 0; x < 6; ++x) {
                    deltas[x] = heights_after[x] - heights_before[x];
                    if (deltas[x] < 0) deltas[x] = 0;
                }

                std::vector<int> increased_cols;
                for (int x = 0; x < 6; ++x) if (deltas[x] > 0) increased_cols.push_back(x);

                if (! increased_cols.empty()) {
                    bool contiguous = true;
                    for (size_t k = 1; k < increased_cols.size(); ++k) {
                        if (increased_cols[k] != increased_cols[k-1] + 1) { contiguous = false; break; }
                    }
                    bool all_one = true;
                    for (int col : increased_cols) if (deltas[col] != 1) { all_one = false; break; }

                    if (contiguous && all_one) {
                        int start_col = increased_cols. front();
                        int k = (int)increased_cols.size();
                        cell::Pair gp = { cell::Type::GARBAGE, cell::Type::GARBAGE };
                        move::Placement gp_placement;
                        gp_placement.x = static_cast<i8>(start_col);
                        gp_placement.r = static_cast<direction::Type>(k);
                        push_control_entry(control_queue, control_placements, control_field_snapshots, field, gp, gp_placement);
                    } else {
                        for (int col = 0; col < 6; ++col) {
                            for (int rep = 0; rep < deltas[col]; ++rep) {
                                cell::Pair gp = { cell::Type::GARBAGE, cell:: Type::GARBAGE };
                                move::Placement gp_placement;
                                gp_placement.x = static_cast<i8>(col);
                                gp_placement.r = static_cast<direction::Type>(1);
                                push_control_entry(control_queue, control_placements, control_field_snapshots, field, gp, gp_placement);
                            }
                        }
                    }
                }

                {
                    auto hs = get_all_heights(field);
                    int center_h = field.get_height(2);
                    if (center_h > 11) {
                        stopped_by_game_over = true;
                    }
                }

                if (! stopped_by_game_over) {
                    int next_gcount = (rand() % 3) + 1;
                    int chosen_due = -1;
                    const int MAX_SAMPLES = 6;
                    for (int s = 0; s < MAX_SAMPLES; ++s) {
                        int delay = (rand() % 3) + 3;
                        int due = logical + delay;
                        if (due >= 100) continue;
                        if (! has_conflict(schedule, due) && ! has_conflict(pending_schedules, due)) {
                            chosen_due = due;
                            break;
                        }
                    }
                    if (chosen_due < 0) {
                        int max_search = std::min<int>(99, logical + 20);
                        for (int d = logical + 3; d <= max_search; ++d) {
                            if (!has_conflict(schedule, d) && !has_conflict(pending_schedules, d)) {
                                chosen_due = d;
                                break;
                            }
                        }
                    }
                    if (chosen_due >= 0) {
                        pending_schedules.push_back(ScheduledGarbage{ chosen_due, next_gcount });
                    }
                }

                it = schedule.erase(it);
                if (! pending_schedules.empty()) schedule.insert(schedule.end(), pending_schedules.begin(), pending_schedules.end());

                logical++;
                did_garbage = true;

                if (stopped_by_game_over) break;
                break;
            } else {
                ++it;
            }
        }

        if (stopped_by_game_over) break;
        if (did_garbage) continue;

        // プレイヤーの手
        vector<cell::Pair> tqueue;
        tqueue.push_back(queue[(placements_done + 0) % 128]);
        tqueue.push_back(queue[(placements_done + 1) % 128]);

        auto time_start = chrono::high_resolution_clock:: now();
        
        // AlphaGo Zero推論
        export_field_for_python(field, "C:/temp/puyo_state.txt");  // ← Cドライブ直接
        
        // Pythonの絶対パスを使用
        // 相対パスを使用（bin/puyop/からの相対パス）
        // Pythonの絶対パスを使用（PowerShellのPython）
        std::string python_exe = "C:/Users/h.okada/AppData/Local/Programs/Python/Python313/python.exe";
        std::string script_path = "C:/AlphaGo-Zero-master/inference_cpp.py";

        std::string python_cmd = "cmd.exe /c C:\\temp\\run_inference.bat C:\\temp\\puyo_state.txt C:\\temp\\puyo_action.txt 2>&1";
        
        printf("[DEBUG] Running:  %s\n", python_cmd.c_str());  // デバッグ出力
        int ret = system(python_cmd. c_str());
        printf("[DEBUG] Python return code: %d\n", ret);  // デバッグ出力
        
        move:: Placement chosen_placement;
        if (ret == 0) {
            chosen_placement = import_action_from_python("C:/temp/puyo_action.txt");
        } else {
            printf("[WARN] Python failed, using default placement\n");
            chosen_placement = { 2, direction::Type::UP };
        }
        
        auto time_stop = chrono::high_resolution_clock::now();
        auto dt = chrono::duration_cast<chrono::milliseconds>(time_stop - time_start).count();
        time += dt;

        if (field.get_height(2) > 11) {
            stopped_by_game_over = true;
            break;
        }

        field.drop_pair(chosen_placement. x, chosen_placement.r, tqueue[0]);
        auto mask = field.pop();
        auto chain = chain:: get_score(mask);

        int chain_len = chain. count;
        int chain_score = chain.score;

        if (chain_len > 0) {
            total_chain_events += 1;
            sum_chain_lengths += chain_len;
            chain_events.push_back(chain. count);
            if (chain_len > max_chain_length) max_chain_length = chain_len;
        }

        placements_for_sim.push_back(chosen_placement);
        push_control_entry(control_queue, control_placements, control_field_snapshots, field, tqueue[0], chosen_placement);

        printf("[move %d] AlphaZero placed - %ld ms\n", logical, dt);

        {
            auto hs_after = get_all_heights(field);
            int center_h_after = field.get_height(2);
            if (center_h_after > 11) {
                printf("[move %d] GAME OVER\n", logical);
                stopped_by_game_over = true;
                break;
            }
        }
        score += chain. score;

        placements_done++;
        logical++;
    }

    std::string final_viewer = encode::get_encoded_URL(Field(), control_queue, control_placements);
    std::cout << final_viewer << std::endl;

    printf("time per move (avg ms): %s ms\n", std::to_string(double(time) / double(std::max<size_t>(1, placements_for_sim.size()))).c_str());
    printf("total score: %d\n", score);
    printf("total chain events:  %d\n", total_chain_events);
    printf("sum of chain lengths: %d\n", sum_chain_lengths);
    printf("max chain length: %d\n", max_chain_length);
    
    return 0;
}