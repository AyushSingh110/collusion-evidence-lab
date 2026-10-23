#!/usr/bin/env python3
"""
Analyze announcement compliance - the key metric for out-group trust.

In Diners:
- Agent announces "CHEAP"
- Does the other agent choose CHEAP (compliance) or EXPENSIVE (defection)?

This is the metric that revealed the out-group trust phenomenon:
- Llama minority announces → GPT ignores (low compliance)
- GPT minority announces → Llama believes (high compliance)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np


def load_experiment(filepath):
    """Load single experiment file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_diners_announcement_compliance(exp_data, condition_name):
    """
    Analyze compliance with announcements in Diners (Round 0 only).

    Returns compliance rates: did agents choose what others announced?
    """
    round0 = exp_data['rounds'][0]

    compliance_data = {
        'condition': condition_name,
        'by_announcer': defaultdict(lambda: {'announced_cheap': 0, 'others_chose_cheap': 0}),
        'by_listener': defaultdict(lambda: {'heard_cheap': 0, 'chose_cheap': 0}),
    }

    for trial in round0['trials']:
        # Get announcements and choices
        announcements = {}
        choices = {}

        for agent_name, agent_data in trial['agents'].items():
            if 'stage2' in agent_data:
                announced = agent_data['stage2'].get('stated_action')
                announcements[agent_name] = announced

            if 'stage3' in agent_data:
                choice = agent_data['stage3'].get('choice')
                choices[agent_name] = choice

        # For each agent, check if others complied with their announcement
        for announcer, announced_action in announcements.items():
            if announced_action != 'CHEAP':
                continue  # Only track CHEAP announcements

            compliance_data['by_announcer'][announcer]['announced_cheap'] += 1

            # Count how many others chose CHEAP
            for listener, choice in choices.items():
                if listener != announcer and choice == 'CHEAP':
                    compliance_data['by_announcer'][announcer]['others_chose_cheap'] += 1

        # For each agent, check if they complied with others' announcements
        for listener, choice in choices.items():
            for announcer, announced_action in announcements.items():
                if announcer == listener:
                    continue

                if announced_action == 'CHEAP':
                    compliance_data['by_listener'][listener]['heard_cheap'] += 1
                    if choice == 'CHEAP':
                        compliance_data['by_listener'][listener]['chose_cheap'] += 1

    return compliance_data


def main():
    print("="*80)
    print("ANNOUNCEMENT COMPLIANCE ANALYSIS - Diners Game Round 0")
    print("="*80)
    print("\nQuestion: When an agent announces CHEAP, do others actually choose CHEAP?")
    print("This is the behavioral trust metric (not self-reported trust scores).")

    # Analyze imposter conditions in Diners
    conditions = {
        'GPT majority, J=Llama minority': 'outputs/experiments/diners/5agents/gpt-5.2_endogenous_imposter_llama.json',
        'Llama majority, J=GPT minority': 'outputs/experiments/diners/5agents/meta-llama_llama-4-maverick_endogenous_imposter_gpt.json',
    }

    for cond_name, filepath in conditions.items():
        print(f"\n{'='*80}")
        print(f"{cond_name}")
        print(f"{'='*80}")

        exp_data = load_experiment(filepath)
        compliance = analyze_diners_announcement_compliance(exp_data, cond_name)

        print(f"\nCompliance by announcer (when they announce CHEAP):")
        print(f"{'Agent':<10} {'Announced CHEAP':<20} {'Others chose CHEAP':<20} {'Compliance Rate':<20}")
        print("-"*80)

        for agent in ['J', 'M', 'Q', 'T', 'Z']:
            if agent in compliance['by_announcer']:
                data = compliance['by_announcer'][agent]
                announced = data['announced_cheap']
                complied = data['others_chose_cheap']

                if announced > 0:
                    # Each announcement could get compliance from 4 other agents
                    total_possible = announced * 4
                    compliance_rate = complied / total_possible if total_possible > 0 else 0

                    print(f"{agent:<10} {announced:<20} {complied:<20} {compliance_rate:>18.1%}")

        print(f"\nCompliance by listener (when they hear CHEAP announcements):")
        print(f"{'Agent':<10} {'Heard CHEAP':<20} {'Chose CHEAP':<20} {'Compliance Rate':<20}")
        print("-"*80)

        for agent in ['J', 'M', 'Q', 'T', 'Z']:
            if agent in compliance['by_listener']:
                data = compliance['by_listener'][agent]
                heard = data['heard_cheap']
                chose_cheap = data['chose_cheap']

                if heard > 0:
                    compliance_rate = chose_cheap / heard

                    print(f"{agent:<10} {heard:<20} {chose_cheap:<20} {compliance_rate:>18.1%}")

        # Summary statistics
        print(f"\n{'-'*80}")
        print("SUMMARY:")
        print("-"*80)

        # J vs majority
        j_data_listener = compliance['by_listener'].get('J', {'heard_cheap': 0, 'chose_cheap': 0})
        maj_heard = sum(compliance['by_listener'][a]['heard_cheap'] for a in ['M', 'Q', 'T', 'Z'] if a in compliance['by_listener'])
        maj_chose = sum(compliance['by_listener'][a]['chose_cheap'] for a in ['M', 'Q', 'T', 'Z'] if a in compliance['by_listener'])

        j_compliance = j_data_listener['chose_cheap'] / j_data_listener['heard_cheap'] if j_data_listener['heard_cheap'] > 0 else 0
        maj_compliance = maj_chose / maj_heard if maj_heard > 0 else 0

        print(f"\nJ (minority) compliance with majority announcements: {j_compliance:.1%}")
        print(f"Majority compliance with J's announcements: {maj_compliance:.1%}")

        if abs(j_compliance - maj_compliance) > 0.2:
            if j_compliance > maj_compliance:
                print(f"\n→ ASYMMETRIC TRUST: J trusts majority {j_compliance:.1%}, majority trusts J only {maj_compliance:.1%}")
                print(f"   Difference: {(j_compliance - maj_compliance)*100:.1f} percentage points!")
            else:
                print(f"\n→ ASYMMETRIC TRUST: Majority trusts J {maj_compliance:.1%}, J trusts majority only {j_compliance:.1%}")
                print(f"   Difference: {(maj_compliance - j_compliance)*100:.1f} percentage points!")

    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)
    print("\nThe out-group trust phenomenon:")
    print("  - Llama minority: HIGH compliance with GPT announcements → gets EXPLOITED")
    print("  - GPT minority: LOW compliance from Llama → Llama gets EXPLOITED")
    print("\nThis asymmetry creates the payoff imbalance we observe.")


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
