#!/usr/bin/env python3
"""
Employee Shift Scheduler - Python version

Features:
- Days: Monday..Sunday
- Shifts: morning, afternoon, evening
- Collects employee preferences (single or ranked)
- Ensures no employee >1 shift/day and <=5 days/week
- Ensures at least 2 employees per shift/day; if fewer, randomly assigns extra (respecting max days)
- Resolves conflicts when preferred shift is full by trying ranked prefs -> other shifts same day -> next day
- Configurable MAX_PER_SHIFT (default 4)
"""

import random
from collections import defaultdict, Counter
import copy

random.seed(42)  # deterministic demo behavior; remove for true randomness

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SHIFTS = ["morning", "afternoon", "evening"]
MAX_PER_SHIFT = 4  # maximum employees allowed per shift per day (defines "full")
MIN_PER_SHIFT = 2  # minimum required per shift per day

# Example demo employees with ranked preferences for each day.
# Format: { "akash": [ ["morning"], ["morning","afternoon"], ... 7 items ] }
# Each day's entry can be a list (ranked) or a single-string (treated as single preferred)
DEMO_EMPLOYEES = {
    "akash":   [["morning"], ["morning"], ["afternoon"], ["morning"], ["evening"], ["morning"], ["morning"]],
    "bipin":   [["morning"], ["morning","afternoon"], ["morning"], ["afternoon"], ["afternoon"], ["evening"], ["afternoon"]],
    "chandu":  [["evening"], ["evening"], ["evening"], ["evening"], ["morning"], ["afternoon"], ["evening"]],
    "damu":    [["afternoon"], ["afternoon"], ["afternoon"], ["afternoon"], ["afternoon"], ["afternoon"], ["afternoon"]],
    "evan":    [["morning","afternoon","evening"]] * 7,
    "farida":  [["afternoon","morning"]] * 7,
    "ganga":   [["evening","morning"]] * 7,
    "harsha":  [["morning"]] * 7,
    "isha":    [["evening"]] * 7,
    "jashu":   [["afternoon"]] * 7,
}


def normalize_prefs(raw):
    """Ensure each entry is a list of ranked preferences for 7 days."""
    prefs = {}
    for name, days in raw.items():
        if len(days) != 7:
            raise ValueError(f"Employee {name} must have 7 day preferences.")
        norm = []
        for d in days:
            if isinstance(d, str):
                norm.append([d])
            elif isinstance(d, list):
                # filter to valid shifts and keep order
                norm.append([s for s in d if s in SHIFTS])
            else:
                raise ValueError("Invalid preference format")
        prefs[name] = norm
    return prefs

class Scheduler:
    def __init__(self, prefs, max_per_shift=MAX_PER_SHIFT, min_per_shift=MIN_PER_SHIFT):
        self.prefs = prefs  # dict name -> list of 7 lists (ranked)
        self.names = list(prefs.keys())
        self.num_emp = len(self.names)
        self.max_per_shift = max_per_shift
        self.min_per_shift = min_per_shift

        # schedule[day_index][shift] = list of employee names
        self.schedule = [ { s: [] for s in SHIFTS } for _ in DAYS ]
        # track days worked per employee
        self.days_worked = Counter()
        # track assignment per day to ensure <=1 shift/day: assigned_today[(day, name)] = True
        self.assigned_today = set()

    def can_assign(self, name, day_idx, shift):
        # not already assigned that day
        if (day_idx, name) in self.assigned_today:
            return False
        # hasn't exceeded 5 days
        if self.days_worked[name] >= 5:
            return False
        # shift capacity
        if len(self.schedule[day_idx][shift]) >= self.max_per_shift:
            return False
        return True

    def assign(self, name, day_idx, shift):
        if not self.can_assign(name, day_idx, shift):
            return False
        self.schedule[day_idx][shift].append(name)
        self.assigned_today.add((day_idx, name))
        self.days_worked[name] += 1
        return True

    def first_pass_preferences(self):
        # Try to assign each employee to their top preference for each day (respect ranked order),
        # but only if not full and employee allowed.
        # We'll iterate employees then days to honor fairness.
        for name in self.names:
            for day_idx in range(7):
                ranked = self.prefs[name][day_idx]
                assigned = False
                for shift in ranked:
                    if self.assign(name, day_idx, shift):
                        assigned = True
                        break
                # if couldn't assign to any preferred shift because full, leave for conflict resolution
        # end

    def enforce_minimums(self):
        # For every day & shift, ensure at least min_per_shift employees. If fewer, randomly pick
        # available employees (not assigned that day and days_worked <5) and assign them.
        for day_idx in range(7):
            for shift in SHIFTS:
                while len(self.schedule[day_idx][shift]) < self.min_per_shift:
                    candidates = [n for n in self.names
                                  if self.can_assign(n, day_idx, shift)]
                    if not candidates:
                        # No one available to fill; break to avoid infinite loop
                        break
                    pick = random.choice(candidates)
                    self.assign(pick, day_idx, shift)

    def resolve_conflicts(self):
        # A more systematic pass: for every employee/day not assigned yet, try to find a slot:
        for name in self.names:
            for day_idx in range(7):
                if (day_idx, name) in self.assigned_today:
                    continue  # already assigned
                # Try ranked prefs for same day
                ranked = self.prefs[name][day_idx]
                assigned = False
                for shift in ranked:
                    if self.can_assign(name, day_idx, shift):
                        self.assign(name, day_idx, shift)
                        assigned = True
                        break
                if assigned:
                    continue
                # try other shifts same day
                for shift in SHIFTS:
                    if shift in ranked: 
                        continue
                    if self.can_assign(name, day_idx, shift):
                        self.assign(name, day_idx, shift)
                        assigned = True
                        break
                if assigned:
                    continue
                # try next day(s)
                for d2 in range(day_idx+1, 7):
                    # try ranked of that next day, then others
                    for shift in self.prefs[name][d2]:
                        if self.can_assign(name, d2, shift):
                            self.assign(name, d2, shift)
                            assigned = True
                            break
                    if assigned:
                        break
                    for shift in SHIFTS:
                        if self.can_assign(name, d2, shift):
                            self.assign(name, d2, shift)
                            assigned = True
                            break
                    if assigned:
                        break
                # If still not assigned, okay — they may have reached 5 days or no slots

    def fill_remaining_minimums(self):
        # After conflict resolution, ensure minimums again (because we may have created new shortages)
        self.enforce_minimums()

    def run(self):
        # Clean state
        self.schedule = [ { s: [] for s in SHIFTS } for _ in DAYS ]
        self.days_worked = Counter()
        self.assigned_today = set()

        # 1) First pass: place people to their preferences as possible
        self.first_pass_preferences()
        # 2) Ensure minimum staffing
        self.enforce_minimums()
        # 3) Resolve conflicts for unassigned employees
        self.resolve_conflicts()
        # 4) Final pass to ensure minimums again
        self.fill_remaining_minimums()

    def pretty_print(self):
        out_lines = []
        header = "Day      | Morning             | Afternoon           | Evening"
        out_lines.append(header)
        out_lines.append("-"*len(header))
        for i, day in enumerate(DAYS):
            row = f"{day:<8}| "
            for shift in SHIFTS:
                names = ", ".join(self.schedule[i][shift]) if self.schedule[i][shift] else "(none)"
                row += f"{names:<20}| "
            out_lines.append(row)
        # Also output days worked
        out_lines.append("\nDays worked per employee (name: days):")
        for name in sorted(self.names):
            out_lines.append(f" - {name}: {self.days_worked[name]}")
        return "\n".join(out_lines)


def demo_run():
    prefs = normalize_prefs(DEMO_EMPLOYEES)
    s = Scheduler(prefs)
    s.run()
    print(s.pretty_print())

if __name__ == "__main__":
    print("=== Employee Scheduler (Python demo) ===")
    print("Using demo employees. To use custom input, modify DEMO_EMPLOYEES in the script.")
    demo_run()
