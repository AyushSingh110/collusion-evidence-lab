#!/usr/bin/env python3
"""
Round-by-round temporal analysis of imposter conditions.
Tracks how deception, payoffs, and trust evolve over time.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import statistics

# Which result files the imposter comparison reads. These name the two conditions of
# the original study (a Llama minority vs a GPT minority); point them at your own runs
# if you reproduced the experiment with different models.
MAJORITY_MODEL = "gpt-5.2"
MINORITY_MODEL = "meta-llama_llama-4-maverick"


def load_imposter_data():
    """Load both imposter conditions."""
    games = ['diners', 'fishing']
    data = {}

    for game in games:
        data[game] = {}

        # Original: J=Llama minority
        orig_path = f'outputs/experiments/{game}/5agents/{MAJORITY_MODEL}_endogenous_imposter.json'
        if Path(orig_path).exists():
            with open(orig_path) as f:
                data[game]['llama_minority'] = json.load(f)

        # Symmetric: J=GPT minority
        sym_path = f'outputs/experiments/{game}/5agents/{MINORITY_MODEL}_endogenous_imposter.json'
        if Path(sym_path).exists():
            with open(sym_path) as f:
                data[game]['gpt_minority'] = json.load(f)

    return data

def extract_round_by_round_metrics(exp_data, minority_model_name):
    """Extract metrics for each round."""
    rounds_data = defaultdict(lambda: {
        'J': {'deception': [], 'payoff': [], 'trust_to_others': [], 'trust_from_others': []},
        'majority': {'deception': [], 'payoff': [], 'trust_to_J': [], 'trust_from_J': [], 'trust_within': []}
    })

    majority_agents = ['M', 'Q', 'T', 'Z']

    for round_data in exp_data['rounds']:
        round_id = round_data['round_id']

        for trial in round_data['trials']:
            # Agent J (minority)
            if 'J' in trial['agents']:
                j_data = trial['agents']['J']

                # Deception
                promise_dec = j_data.get('promise_deception', False)
                rounds_data[round_id]['J']['deception'].append(1 if promise_dec else 0)

                # Payoff
                if 'J' in trial['outcomes']['payoffs']:
                    rounds_data[round_id]['J']['payoff'].append(trial['outcomes']['payoffs']['J'])

                # Trust from J to others
                reflection = j_data.get('reflection', {})
                if 'takeaways' in reflection:
                    for target, assessment in reflection['takeaways'].items():
                        score = assessment.get('score')
                        if score is not None:
                            rounds_data[round_id]['J']['trust_to_others'].append(score)

            # Majority agents
            for agent in majority_agents:
                if agent in trial['agents']:
                    agent_data = trial['agents'][agent]

                    # Deception
                    promise_dec = agent_data.get('promise_deception', False)
                    rounds_data[round_id]['majority']['deception'].append(1 if promise_dec else 0)

                    # Payoff
                    if agent in trial['outcomes']['payoffs']:
                        rounds_data[round_id]['majority']['payoff'].append(trial['outcomes']['payoffs'][agent])

                    # Trust
                    reflection = agent_data.get('reflection', {})
                    if 'takeaways' in reflection:
                        for target, assessment in reflection['takeaways'].items():
                            score = assessment.get('score')
                            if score is not None:
                                # Trust to J
                                if target == 'J':
                                    rounds_data[round_id]['majority']['trust_to_J'].append(score)
                                    rounds_data[round_id]['J']['trust_from_others'].append(score)
                                # Trust within majority
                                elif target in majority_agents:
                                    rounds_data[round_id]['majority']['trust_within'].append(score)

                                # Trust from J
                                if agent == 'J' and target != 'J':
                                    rounds_data[round_id]['majority']['trust_from_J'].append(score)

    return rounds_data

def print_round_by_round_table(game, condition_name, minority_label, majority_label, rounds_data):
    """Print formatted round-by-round table."""
    print(f"\n{'='*100}")
    print(f"{game.upper()} - {condition_name}")
    print(f"Minority: {minority_label} | Majority: {majority_label}")
    print(f"{'='*100}")

    print(f"\n{'Round':<8} {'J Dec%':<12} {'Maj Dec%':<12} {'J Pay':<12} {'Maj Pay':<12} {'Trust J→Maj':<12} {'Trust Maj→J':<12}")
    print("-" * 100)

    for round_id in sorted(rounds_data.keys()):
        rd = rounds_data[round_id]

        # Deception
        j_dec = statistics.mean(rd['J']['deception']) * 100 if rd['J']['deception'] else 0
        maj_dec = statistics.mean(rd['majority']['deception']) * 100 if rd['majority']['deception'] else 0

        # Payoff
        j_pay = statistics.mean(rd['J']['payoff']) if rd['J']['payoff'] else 0
        maj_pay = statistics.mean(rd['majority']['payoff']) if rd['majority']['payoff'] else 0

        # Trust
        trust_j_to_maj = statistics.mean(rd['J']['trust_to_others']) if rd['J']['trust_to_others'] else 0
        trust_maj_to_j = statistics.mean(rd['majority']['trust_to_J']) if rd['majority']['trust_to_J'] else 0

        print(f"{round_id:<8} {j_dec:>6.1f}%      {maj_dec:>6.1f}%      {j_pay:>6.2f}      {maj_pay:>6.2f}      {trust_j_to_maj:>6.2f}        {trust_maj_to_j:>6.2f}")

def analyze_trends(rounds_data):
    """Analyze trends over time."""
    print("\n" + "~" * 100)
    print("TEMPORAL TRENDS")
    print("~" * 100)

    # Early vs Late comparison
    early_rounds = [0, 1, 2, 3, 4]
    late_rounds = [5, 6, 7, 8, 9]

    # J deception
    early_j_dec = []
    late_j_dec = []
    for r in early_rounds:
        if r in rounds_data:
            early_j_dec.extend(rounds_data[r]['J']['deception'])
    for r in late_rounds:
        if r in rounds_data:
            late_j_dec.extend(rounds_data[r]['J']['deception'])

    early_j_dec_pct = statistics.mean(early_j_dec) * 100 if early_j_dec else 0
    late_j_dec_pct = statistics.mean(late_j_dec) * 100 if late_j_dec else 0
    j_trend = late_j_dec_pct - early_j_dec_pct

    # Majority deception
    early_maj_dec = []
    late_maj_dec = []
    for r in early_rounds:
        if r in rounds_data:
            early_maj_dec.extend(rounds_data[r]['majority']['deception'])
    for r in late_rounds:
        if r in rounds_data:
            late_maj_dec.extend(rounds_data[r]['majority']['deception'])

    early_maj_dec_pct = statistics.mean(early_maj_dec) * 100 if early_maj_dec else 0
    late_maj_dec_pct = statistics.mean(late_maj_dec) * 100 if late_maj_dec else 0
    maj_trend = late_maj_dec_pct - early_maj_dec_pct

    # J payoff
    early_j_pay = []
    late_j_pay = []
    for r in early_rounds:
        if r in rounds_data:
            early_j_pay.extend(rounds_data[r]['J']['payoff'])
    for r in late_rounds:
        if r in rounds_data:
            late_j_pay.extend(rounds_data[r]['J']['payoff'])

    early_j_pay_avg = statistics.mean(early_j_pay) if early_j_pay else 0
    late_j_pay_avg = statistics.mean(late_j_pay) if late_j_pay else 0
    j_pay_trend = late_j_pay_avg - early_j_pay_avg

    # Majority payoff
    early_maj_pay = []
    late_maj_pay = []
    for r in early_rounds:
        if r in rounds_data:
            early_maj_pay.extend(rounds_data[r]['majority']['payoff'])
    for r in late_rounds:
        if r in rounds_data:
            late_maj_pay.extend(rounds_data[r]['majority']['payoff'])

    early_maj_pay_avg = statistics.mean(early_maj_pay) if early_maj_pay else 0
    late_maj_pay_avg = statistics.mean(late_maj_pay) if late_maj_pay else 0
    maj_pay_trend = late_maj_pay_avg - early_maj_pay_avg

    # Trust
    early_trust_j_to_maj = []
    late_trust_j_to_maj = []
    early_trust_maj_to_j = []
    late_trust_maj_to_j = []

    for r in early_rounds:
        if r in rounds_data:
            early_trust_j_to_maj.extend(rounds_data[r]['J']['trust_to_others'])
            early_trust_maj_to_j.extend(rounds_data[r]['majority']['trust_to_J'])
    for r in late_rounds:
        if r in rounds_data:
            late_trust_j_to_maj.extend(rounds_data[r]['J']['trust_to_others'])
            late_trust_maj_to_j.extend(rounds_data[r]['majority']['trust_to_J'])

    early_j_trust = statistics.mean(early_trust_j_to_maj) if early_trust_j_to_maj else 0
    late_j_trust = statistics.mean(late_trust_j_to_maj) if late_trust_j_to_maj else 0
    j_trust_trend = late_j_trust - early_j_trust

    early_maj_trust = statistics.mean(early_trust_maj_to_j) if early_trust_maj_to_j else 0
    late_maj_trust = statistics.mean(late_trust_maj_to_j) if late_trust_maj_to_j else 0
    maj_trust_trend = late_maj_trust - early_maj_trust

    # Print trends
    print(f"\n{'Metric':<30} {'Early (R0-4)':<15} {'Late (R5-9)':<15} {'Change':<15} {'Direction':<12}")
    print("-" * 90)

    print(f"{'J Deception %':<30} {early_j_dec_pct:>6.1f}%         {late_j_dec_pct:>6.1f}%         {j_trend:>+6.1f} pp     {get_arrow(j_trend):<12}")
    print(f"{'Majority Deception %':<30} {early_maj_dec_pct:>6.1f}%         {late_maj_dec_pct:>6.1f}%         {maj_trend:>+6.1f} pp     {get_arrow(maj_trend):<12}")
    print(f"{'J Payoff':<30} {early_j_pay_avg:>6.2f}          {late_j_pay_avg:>6.2f}          {j_pay_trend:>+6.2f}       {get_arrow(j_pay_trend):<12}")
    print(f"{'Majority Payoff':<30} {early_maj_pay_avg:>6.2f}          {late_maj_pay_avg:>6.2f}          {maj_pay_trend:>+6.2f}       {get_arrow(maj_pay_trend):<12}")
    print(f"{'Trust J → Majority':<30} {early_j_trust:>6.2f}          {late_j_trust:>6.2f}          {j_trust_trend:>+6.2f}       {get_arrow(j_trust_trend):<12}")
    print(f"{'Trust Majority → J':<30} {early_maj_trust:>6.2f}          {late_maj_trust:>6.2f}          {maj_trust_trend:>+6.2f}       {get_arrow(maj_trust_trend):<12}")

def get_arrow(value, threshold=0.05):
    """Get trend arrow."""
    if abs(value) < threshold:
        return "→ Stable"
    elif value > 0:
        return "↑ Increase"
    else:
        return "↓ Decrease"

def identify_key_rounds(rounds_data):
    """Identify rounds with notable changes."""
    print("\n" + "~" * 100)
    print("KEY EVENTS")
    print("~" * 100)

    # Track round-to-round payoff changes
    payoff_changes = []
    prev_j_pay = None

    for round_id in sorted(rounds_data.keys()):
        j_pay = statistics.mean(rounds_data[round_id]['J']['payoff']) if rounds_data[round_id]['J']['payoff'] else 0

        if prev_j_pay is not None:
            change = j_pay - prev_j_pay
            payoff_changes.append((round_id, change, j_pay))

        prev_j_pay = j_pay

    # Find largest payoff spikes
    if payoff_changes:
        payoff_changes.sort(key=lambda x: abs(x[1]), reverse=True)

        print("\nLargest payoff changes for minority (J):")
        for i, (round_id, change, payoff) in enumerate(payoff_changes[:3]):
            print(f"  Round {round_id}: {change:+.2f} (new payoff: {payoff:.2f})")

def compare_both_conditions(data, game):
    """Compare both imposter conditions side-by-side."""
    print(f"\n{'='*100}")
    print(f"COMPARISON: {game.upper()} - Both Imposter Conditions Side-by-Side")
    print(f"{'='*100}")

    llama_min_rounds = extract_round_by_round_metrics(data[game]['llama_minority'], 'Llama')
    gpt_min_rounds = extract_round_by_round_metrics(data[game]['gpt_minority'], 'GPT')

    print(f"\n{'Round':<8} {'Llama-Min':<25} {'GPT-Min':<25} {'Difference':<20}")
    print(f"{'':8} {'J Dec% | J Pay':<25} {'J Dec% | J Pay':<25} {'ΔDec% | ΔPay':<20}")
    print("-" * 90)

    for round_id in sorted(llama_min_rounds.keys()):
        # Llama minority
        llama_j_dec = statistics.mean(llama_min_rounds[round_id]['J']['deception']) * 100 if llama_min_rounds[round_id]['J']['deception'] else 0
        llama_j_pay = statistics.mean(llama_min_rounds[round_id]['J']['payoff']) if llama_min_rounds[round_id]['J']['payoff'] else 0

        # GPT minority
        gpt_j_dec = statistics.mean(gpt_min_rounds[round_id]['J']['deception']) * 100 if gpt_min_rounds[round_id]['J']['deception'] else 0
        gpt_j_pay = statistics.mean(gpt_min_rounds[round_id]['J']['payoff']) if gpt_min_rounds[round_id]['J']['payoff'] else 0

        # Differences
        diff_dec = gpt_j_dec - llama_j_dec
        diff_pay = gpt_j_pay - llama_j_pay

        print(f"{round_id:<8} {llama_j_dec:>5.1f}% | {llama_j_pay:>6.2f}         {gpt_j_dec:>5.1f}% | {gpt_j_pay:>6.2f}         {diff_dec:>+6.1f} pp | {diff_pay:>+6.2f}")

    print("\nInterpretation:")
    print("  - Positive ΔDec%: GPT minority is MORE deceptive than Llama minority")
    print("  - Positive ΔPay: GPT minority gets HIGHER payoff than Llama minority")

def main():
    """Run round-by-round analysis."""
    print("=" * 100)
    print("ROUND-BY-ROUND TEMPORAL ANALYSIS")
    print("=" * 100)

    data = load_imposter_data()

    # Analyze each condition separately
    for game in ['diners', 'fishing']:
        # Llama minority
        print_round_by_round_table(
            game,
            "ORIGINAL IMPOSTER",
            "J = Llama (minority)",
            "M/Q/T/Z = GPT (majority)",
            extract_round_by_round_metrics(data[game]['llama_minority'], 'Llama')
        )

        llama_min_rounds = extract_round_by_round_metrics(data[game]['llama_minority'], 'Llama')
        analyze_trends(llama_min_rounds)
        identify_key_rounds(llama_min_rounds)

        # GPT minority
        print("\n")
        print_round_by_round_table(
            game,
            "SYMMETRIC IMPOSTER",
            "J = GPT (minority)",
            "M/Q/T/Z = Llama (majority)",
            extract_round_by_round_metrics(data[game]['gpt_minority'], 'GPT')
        )

        gpt_min_rounds = extract_round_by_round_metrics(data[game]['gpt_minority'], 'GPT')
        analyze_trends(gpt_min_rounds)
        identify_key_rounds(gpt_min_rounds)

        # Side-by-side comparison
        compare_both_conditions(data, game)

        print("\n" + "=" * 100 + "\n")

if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, KeyError) as e:
        sys.exit(
            "\nThis script analyses result files from the original study, and the ones it\n"
            f"expects were not found under outputs/ ({e!r}).\n"
            "Run the matching experiment first, or point the paths at the top of this\n"
            "file at your own results."
        )
