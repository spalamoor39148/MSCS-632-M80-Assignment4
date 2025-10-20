// scheduler.cpp
// Employee Shift Scheduler - C++ version
//
// Similar behavior to the Python script.
// Build: g++ -std=c++17 scheduler.cpp -o scheduler
// Run: ./scheduler

#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <algorithm>
#include <random>
#include <ctime>
#include <set>
#include <iomanip>   // for setw and formatting
using namespace std;


const vector<string> DAYS = {"Mon","Tue","Wed","Thu","Fri","Sat","Sun"};
const vector<string> SHIFTS = {"morning","afternoon","evening"};
int MAX_PER_SHIFT = 4;
int MIN_PER_SHIFT = 2;
std::mt19937 rng(42);

using Prefs = map<string, vector<vector<string>>>; // name -> 7-day list of ranked prefs

Prefs demo_prefs() {
    Prefs p;
    p["akash"]  = { {"morning"},{"morning"},{"afternoon"},{"morning"},{"evening"},{"morning"},{"morning"} };
    p["bipin"]  = { {"morning"},{"morning","afternoon"},{"morning"},{"afternoon"},{"afternoon"},{"evening"},{"afternoon"} };
    p["chandu"] = { {"evening"},{"evening"},{"evening"},{"evening"},{"morning"},{"afternoon"},{"evening"} };
    p["damu"]   = { {"afternoon"},{"afternoon"},{"afternoon"},{"afternoon"},{"afternoon"},{"afternoon"},{"afternoon"} };
    p["evan"]   = vector<vector<string>>(7, {"morning","afternoon","evening"});
    p["farida"] = vector<vector<string>>(7, {"afternoon","morning"});
    p["ganga"]  = vector<vector<string>>(7, {"evening","morning"});
    p["harsha"] = vector<vector<string>>(7, {"morning"});
    p["isha"]   = vector<vector<string>>(7, {"evening"});
    p["jashu"]  = vector<vector<string>>(7, {"afternoon"});
    return p;
}
struct Scheduler {
    Prefs prefs;
    vector<string> names;
    // schedule[day][shift] = vector<string>
    vector<map<string, vector<string>>> schedule;
    unordered_map<string,int> days_worked;
    set<pair<int,string>> assigned_today;

    Scheduler(const Prefs &p) : prefs(p) {
        for (auto &kv : prefs) names.push_back(kv.first);
        schedule.assign(7, map<string, vector<string>>());
        for (int i=0;i<7;i++){
            for (auto &s : SHIFTS) schedule[i][s] = vector<string>();
        }
        for (auto &n : names) days_worked[n] = 0;
    }

    bool can_assign(const string &name, int day, const string &shift) {
        if (assigned_today.count({day,name})) return false;
        if (days_worked[name] >= 5) return false;
        if ((int)schedule[day][shift].size() >= MAX_PER_SHIFT) return false;
        return true;
    }

    bool assign(const string &name, int day, const string &shift) {
        if (!can_assign(name, day, shift)) return false;
        schedule[day][shift].push_back(name);
        assigned_today.insert({day,name});
        days_worked[name]++;
        return true;
    }

    void first_pass_preferences() {
        for (auto &name : names) {
            for (int d=0; d<7; ++d) {
                auto &ranked = prefs.at(name)[d];
                for (auto &shift : ranked) {
                    if (assign(name, d, shift)) break;
                }
            }
        }
    }

    void enforce_minimums() {
        for (int d=0; d<7; ++d) {
            for (auto &shift : SHIFTS) {
                while ((int)schedule[d][shift].size() < MIN_PER_SHIFT) {
                    vector<string> candidates;
                    for (auto &n : names) {
                        if (can_assign(n,d,shift)) candidates.push_back(n);
                    }
                    if (candidates.empty()) break;
                    uniform_int_distribution<int> dist(0, (int)candidates.size()-1);
                    string pick = candidates[dist(rng)];
                    assign(pick, d, shift);
                }
            }
        }
    }

    void resolve_conflicts() {
        for (auto &name : names) {
            for (int d=0; d<7; ++d) {
                if (assigned_today.count({d,name})) continue;
                bool assigned = false;
                auto &ranked = prefs.at(name)[d];
                for (auto &shift : ranked) {
                    if (can_assign(name,d,shift) && assign(name,d,shift)) { assigned = true; break; }
                }
                if (assigned) continue;
                for (auto &shift : SHIFTS) {
                    if (can_assign(name,d,shift) && assign(name,d,shift)) { assigned = true; break; }
                }
                if (assigned) continue;
                for (int d2=d+1; d2<7 && !assigned; ++d2) {
                    for (auto &shift : prefs.at(name)[d2]) {
                        if (can_assign(name,d2,shift) && assign(name,d2,shift)) { assigned = true; break; }
                    }
                    for (auto &shift : SHIFTS) {
                        if (assigned) break;
                        if (can_assign(name,d2,shift) && assign(name,d2,shift)) { assigned = true; break; }
                    }
                }
            }
        }
    }

    void run() {
        // reset
        for (int i=0;i<7;i++){
            for (auto &s : SHIFTS) schedule[i][s].clear();
        }
        for (auto &kv : days_worked) kv.second = 0;
        assigned_today.clear();

        first_pass_preferences();
        enforce_minimums();
        resolve_conflicts();
        enforce_minimums();
    }

    void print_schedule() {
        cout << left << setw(8) << "Day" << "| " << setw(22) << "Morning" << "| " << setw(22) << "Afternoon" << "| " << "Evening" << "\n";
        cout << string(70,'-') << "\n";
        for (int d=0; d<7; ++d) {
            cout << left << setw(8) << DAYS[d] << "| ";
            for (auto &shift : SHIFTS) {
                string joined = "(none)";
                if (!schedule[d][shift].empty()) {
                    string s;
                    for (size_t i=0;i<schedule[d][shift].size();++i){
                        if (i) s += ", ";
                        s += schedule[d][shift][i];
                    }
                    joined = s;
                }
                cout << setw(22) << joined << "| ";
            }
            cout << "\n";
        }
        cout << "\nDays worked per employee:\n";
        for (auto &name : names) {
            cout << " - " << name << ": " << days_worked[name] << "\n";
        }
    }
};

int main(){
    cout << "=== Employee Scheduler (C++ demo) ===\n";
    auto p = demo_prefs();
    Scheduler s(p);
    s.run();
    s.print_schedule();
    return 0;
}
